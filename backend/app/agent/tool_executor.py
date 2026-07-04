from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from app.agent import safety, service
from app.agent.enums import AgentToolAccessMode, AgentToolCallStatus, AgentToolRiskLevel
from app.agent.exceptions import AgentToolDisabledError, AgentToolError, AgentToolMetadataError, AgentToolNotFoundError
from app.agent.schemas import AgentToolMetadata, ToolExecutionRequest, ToolExecutionResult
from app.agent.tool_registry import AgentToolRegistry
from app.agent.tools.base import AgentTool
from app.modules.permissions import service as permissions_service


SAFE_PERMISSION_DENIED_MESSAGE = "Tool execution is not allowed for this family member context."
SAFE_CONFIRMATION_REQUIRED_MESSAGE = "This tool requires explicit confirmation before it can run."
SAFE_TOOL_FAILED_MESSAGE = "Tool execution failed safely without exposing sensitive details."
SAFE_TOOL_NOT_FOUND_MESSAGE = "Requested tool is not available."
SAFE_TOOL_DISABLED_MESSAGE = "Requested tool is disabled."
SAFE_SAFETY_BLOCKED_MESSAGE = "Tool execution was blocked by the current safety level."
SAFE_TOOL_COMPLETED_MESSAGE = "Tool execution completed."

PermissionChecker = Callable[..., Any]
SENSITIVE_SUMMARY_KEYS = {
    "access_token",
    "api_key",
    "file_path",
    "key",
    "password",
    "password_hash",
    "private_key",
    "raw_extracted_text",
    "refresh_token",
    "secret",
    "session_token",
    "token",
}


class AgentToolExecutor:
    def __init__(
        self,
        registry: AgentToolRegistry,
        *,
        permission_checker: PermissionChecker | None = None,
    ) -> None:
        self.registry = registry
        self.permission_checker = permission_checker or permissions_service.check_member_permission

    def execute(self, db: Session, request: ToolExecutionRequest) -> ToolExecutionResult:
        try:
            tool = self.registry.get_tool(request.tool_name)
        except AgentToolNotFoundError:
            tool_call = self._start_placeholder_call(db, request)
            service.block_tool_call(
                db,
                tool_call.id,
                status=AgentToolCallStatus.BLOCKED_BY_REGISTRY,
                error_type="tool_not_found",
                error_message=SAFE_TOOL_NOT_FOUND_MESSAGE,
                output_summary={"status": "blocked", "reason": "tool_not_found"},
            )
            db.commit()
            return _blocked_result(request.tool_name, tool_call.id, SAFE_TOOL_NOT_FOUND_MESSAGE, "tool_not_found")

        try:
            metadata = self.registry.validate_tool_metadata(tool)
        except AgentToolMetadataError as exc:
            tool_call = self._start_tool_call(db, request, tool.metadata)
            service.block_tool_call(
                db,
                tool_call.id,
                status=AgentToolCallStatus.BLOCKED_BY_REGISTRY,
                error_type=exc.__class__.__name__,
                error_message="tool metadata is invalid",
                output_summary={"status": "blocked", "reason": "invalid_metadata"},
            )
            db.commit()
            return _blocked_result(metadata_name(tool), tool_call.id, SAFE_TOOL_NOT_FOUND_MESSAGE, "invalid_metadata")

        tool_call = self._start_tool_call(db, request, metadata)

        if not metadata.enabled:
            service.block_tool_call(
                db,
                tool_call.id,
                status=AgentToolCallStatus.BLOCKED_BY_REGISTRY,
                error_type=AgentToolDisabledError.__name__,
                error_message=SAFE_TOOL_DISABLED_MESSAGE,
                output_summary={"status": "blocked", "reason": "tool_disabled"},
            )
            db.commit()
            return _blocked_result(metadata.name, tool_call.id, SAFE_TOOL_DISABLED_MESSAGE, "tool_disabled")

        if _safety_blocks_execution(request.safety_level):
            service.block_tool_call(
                db,
                tool_call.id,
                status=AgentToolCallStatus.BLOCKED_BY_GUARD,
                error_type="safety_blocked",
                error_message=SAFE_SAFETY_BLOCKED_MESSAGE,
                output_summary={"status": "blocked", "reason": "safety_blocked"},
            )
            db.commit()
            return _blocked_result(metadata.name, tool_call.id, SAFE_SAFETY_BLOCKED_MESSAGE, "safety_blocked")

        if _requires_confirmation(metadata) and not request.confirmed:
            service.block_tool_call(
                db,
                tool_call.id,
                status=AgentToolCallStatus.BLOCKED_BY_GUARD,
                error_type="confirmation_required",
                error_message=SAFE_CONFIRMATION_REQUIRED_MESSAGE,
                output_summary={"status": "blocked", "reason": "confirmation_required"},
            )
            db.commit()
            return ToolExecutionResult(
                tool_name=metadata.name,
                status="blocked",
                blocked=True,
                requires_confirmation=True,
                message=SAFE_CONFIRMATION_REQUIRED_MESSAGE,
                output_data=None,
                tool_call_id=tool_call.id,
                error_code="confirmation_required",
            )

        permission_result = self._check_permission(db, request, metadata)
        if permission_result is not None and not bool(getattr(permission_result, "allowed", False)):
            summary = _permission_summary(permission_result)
            service.block_tool_call(
                db,
                tool_call.id,
                status=AgentToolCallStatus.BLOCKED_BY_PERMISSION,
                error_type="permission_denied",
                error_message=SAFE_PERMISSION_DENIED_MESSAGE,
                permission_checked=True,
                permission_result=summary,
                output_summary={"status": "blocked", "reason": "permission_denied"},
            )
            db.commit()
            return _blocked_result(metadata.name, tool_call.id, SAFE_PERMISSION_DENIED_MESSAGE, "permission_denied")
        if permission_result is not None:
            tool_call.permission_checked = True
            tool_call.permission_result = _permission_summary(permission_result)

        try:
            validated_input = tool.validate_input(dict(request.input_data))
            output_data = tool.execute(validated_input)
            output_summary = _summarize_mapping(output_data)
            service.complete_tool_call(db, tool_call.id, output_summary=output_summary)
            db.commit()
            return ToolExecutionResult(
                tool_name=metadata.name,
                status="completed",
                blocked=False,
                requires_confirmation=False,
                message=SAFE_TOOL_COMPLETED_MESSAGE,
                output_data=output_data,
                tool_call_id=tool_call.id,
            )
        except Exception as exc:
            service.fail_tool_call(
                db,
                tool_call.id,
                error_type=exc.__class__.__name__,
                error_message="tool execution failed",
                output_summary={"status": "failed", "reason": "tool_execution_failed"},
            )
            db.commit()
            return ToolExecutionResult(
                tool_name=metadata.name,
                status="failed",
                blocked=True,
                requires_confirmation=False,
                message=SAFE_TOOL_FAILED_MESSAGE,
                output_data=None,
                tool_call_id=tool_call.id,
                error_code="tool_execution_failed",
            )

    def _start_tool_call(self, db: Session, request: ToolExecutionRequest, metadata: AgentToolMetadata):
        return service.start_tool_call(
            db,
            trace_id=request.trace_id,
            tool_name=metadata.name,
            access_mode=_access_mode(metadata.access_mode),
            risk_level=_risk_level(metadata.risk_level),
            current_user_id=request.actor_user_id,
            target_user_id=request.target_user_id,
            input_summary=_summarize_mapping(request.input_data),
        )

    def _start_placeholder_call(self, db: Session, request: ToolExecutionRequest):
        return service.start_tool_call(
            db,
            trace_id=request.trace_id,
            tool_name=request.tool_name,
            access_mode=AgentToolAccessMode.READ,
            risk_level=AgentToolRiskLevel.LOW,
            current_user_id=request.actor_user_id,
            target_user_id=request.target_user_id,
            input_summary=_summarize_mapping(request.input_data),
        )

    def _check_permission(self, db: Session, request: ToolExecutionRequest, metadata: AgentToolMetadata) -> Any | None:
        if metadata.category == "system":
            return None
        if not metadata.required_permission_type or not metadata.required_permission_action:
            raise AgentToolError("tool permission declaration is required")
        if request.actor_user_id != request.target_user_id and request.family_id is None:
            return _DeniedPermissionResult("missing_family_context")
        return self.permission_checker(
            db,
            current_user_id=request.actor_user_id,
            family_id=request.family_id,
            target_user_id=request.target_user_id,
            permission_type=metadata.required_permission_type,
            action=metadata.required_permission_action,
        )


class _DeniedPermissionResult:
    allowed = False
    permission_type = None
    action = None
    visibility_scope = None
    safe_message = SAFE_PERMISSION_DENIED_MESSAGE

    def __init__(self, reason: str) -> None:
        self.reason = reason


def _requires_confirmation(metadata: AgentToolMetadata) -> bool:
    return metadata.requires_confirmation or metadata.access_mode in {"write", "draft"} or metadata.risk_level in {"high", "critical"}


def _safety_blocks_execution(safety_level: str | None) -> bool:
    return str(safety_level or "").lower() in {"blocked", "high_risk", "emergency"}


def _access_mode(value: str) -> AgentToolAccessMode:
    if value == "none":
        return AgentToolAccessMode.READ
    if value == "admin":
        return AgentToolAccessMode.CONTROL
    return AgentToolAccessMode(value)


def _risk_level(value: str) -> AgentToolRiskLevel:
    return AgentToolRiskLevel(value)


def _permission_summary(permission_result: Any) -> dict[str, Any]:
    return {
        "allowed": bool(getattr(permission_result, "allowed", False)),
        "permission_type": getattr(permission_result, "permission_type", None),
        "action": getattr(permission_result, "action", None),
        "reason": getattr(permission_result, "reason", None),
        "visibility_scope": getattr(permission_result, "visibility_scope", None),
    }


def _summarize_mapping(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    summary: dict[str, Any] = {}
    redacted_count = 0
    for key, item in value.items():
        key_text = str(key)
        if _is_sensitive_summary_key(key_text):
            redacted_count += 1
            summary[f"redacted_field_{redacted_count}"] = {"type": "redacted", "reason": "sensitive_field"}
            continue
        summary[key_text] = _summarize_value(item)
    return summary


def _summarize_value(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        decision = safety.AgentSafetyPolicy().evaluate_output(value)
        excerpt = "[unsafe_medical_content_removed]" if decision.blocked else safety.excerpt_text(value, max_length=80)
        return {
            "type": "str",
            "length": len(value),
            "excerpt": excerpt,
        }
    if isinstance(value, (int, float, bool)) or value is None:
        return {"type": type(value).__name__, "value": value}
    if isinstance(value, (list, tuple, set)):
        return {"type": "list", "length": len(value)}
    if isinstance(value, dict):
        safe_keys = [str(key) for key in value.keys() if not _is_sensitive_summary_key(str(key))]
        redacted_count = len(value) - len(safe_keys)
        summary: dict[str, Any] = {"type": "dict", "keys": sorted(safe_keys)}
        if redacted_count:
            summary["redacted_fields"] = redacted_count
        return summary
    return {"type": type(value).__name__}


def _is_sensitive_summary_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return normalized in SENSITIVE_SUMMARY_KEYS or normalized.endswith("_token") or normalized.endswith("_key")


def _blocked_result(tool_name: str, tool_call_id, message: str, error_code: str) -> ToolExecutionResult:
    return ToolExecutionResult(
        tool_name=tool_name,
        status="blocked",
        blocked=True,
        requires_confirmation=False,
        message=message,
        output_data=None,
        tool_call_id=tool_call_id,
        error_code=error_code,
    )


def metadata_name(tool: AgentTool) -> str:
    metadata = getattr(tool, "metadata", None)
    return getattr(metadata, "name", "unknown_tool")

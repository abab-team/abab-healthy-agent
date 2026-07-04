from __future__ import annotations

from app.agent.exceptions import (
    AgentToolAlreadyRegisteredError,
    AgentToolDisabledError,
    AgentToolMetadataError,
    AgentToolNotFoundError,
    AgentToolPermissionDeclarationError,
)
from app.agent.schemas import AgentToolMetadata
from app.agent.tools.base import AgentTool


VALID_CATEGORIES = {
    "health_profile",
    "health_data",
    "health_record",
    "medical_timeline",
    "document",
    "report",
    "alert",
    "system",
}
VALID_ACCESS_MODES = {"read", "write", "draft", "admin"}
VALID_RISK_LEVELS = {"low", "medium", "high", "critical"}
PERMISSION_REQUIRED_ACCESS_MODES = {"write", "draft"}
CONFIRMATION_REQUIRED_RISK_LEVELS = {"high", "critical"}


class AgentToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, AgentTool] = {}

    def register(self, tool: AgentTool) -> AgentTool:
        metadata = self.validate_tool_metadata(tool)
        if metadata.name in self._tools:
            raise AgentToolAlreadyRegisteredError(f"tool already registered: {metadata.name}")
        self._tools[metadata.name] = tool
        return tool

    def get_tool(self, name: str) -> AgentTool:
        tool = self._tools.get(name)
        if tool is None:
            raise AgentToolNotFoundError(f"tool not found: {name}")
        return tool

    def list_tools(self) -> list[AgentTool]:
        return list(self._tools.values())

    def list_enabled_tools(self) -> list[AgentTool]:
        return [tool for tool in self._tools.values() if tool.metadata.enabled]

    def list_tools_by_category(self, category: str) -> list[AgentTool]:
        normalized = _normalize_value(category, VALID_CATEGORIES, "category")
        return [tool for tool in self._tools.values() if tool.metadata.category == normalized]

    def list_tools_by_access_mode(self, access_mode: str) -> list[AgentTool]:
        normalized = _normalize_value(access_mode, VALID_ACCESS_MODES, "access_mode")
        return [tool for tool in self._tools.values() if tool.metadata.access_mode == normalized]

    def list_tools_by_risk_level(self, risk_level: str) -> list[AgentTool]:
        normalized = _normalize_value(risk_level, VALID_RISK_LEVELS, "risk_level")
        return [tool for tool in self._tools.values() if tool.metadata.risk_level == normalized]

    def ensure_tool_allowed(self, name: str) -> AgentTool:
        tool = self.get_tool(name)
        if not tool.metadata.enabled:
            raise AgentToolDisabledError(f"tool is disabled: {name}")
        return tool

    def validate_tool_metadata(self, tool: AgentTool) -> AgentToolMetadata:
        metadata = getattr(tool, "metadata", None)
        if not isinstance(metadata, AgentToolMetadata):
            raise AgentToolMetadataError("tool metadata must be AgentToolMetadata")
        if not metadata.name.strip():
            raise AgentToolMetadataError("tool name is required")
        if not metadata.description.strip():
            raise AgentToolMetadataError("tool description is required")
        _normalize_value(metadata.category, VALID_CATEGORIES, "category")
        _normalize_value(metadata.access_mode, VALID_ACCESS_MODES, "access_mode")
        _normalize_value(metadata.risk_level, VALID_RISK_LEVELS, "risk_level")
        if _requires_permission(metadata) and not _has_permission_declaration(metadata):
            raise AgentToolPermissionDeclarationError("tool permission declaration is required")
        if metadata.risk_level in CONFIRMATION_REQUIRED_RISK_LEVELS and not metadata.requires_confirmation:
            raise AgentToolMetadataError("high and critical risk tools require confirmation")
        return metadata


def _requires_permission(metadata: AgentToolMetadata) -> bool:
    if metadata.access_mode in PERMISSION_REQUIRED_ACCESS_MODES:
        return True
    return metadata.category != "system"


def _has_permission_declaration(metadata: AgentToolMetadata) -> bool:
    return bool(metadata.required_permission_type and metadata.required_permission_action)


def _normalize_value(value: str, allowed: set[str], field_name: str) -> str:
    normalized = str(value)
    if normalized not in allowed:
        raise AgentToolMetadataError(f"invalid tool {field_name}: {normalized}")
    return normalized

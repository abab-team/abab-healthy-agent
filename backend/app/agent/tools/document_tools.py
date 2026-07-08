from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.api.sanitizers import sanitize_optional_json, sanitize_optional_text, sanitize_required_text
from app.agent.schemas import AgentToolMetadata
from app.agent.tools.base import AgentTool
from app.modules.document_center import service as document_service
from app.modules.document_processing import service as document_processing_service
from app.modules.medical_timeline.enums import MedicalEventType


class MedicalEventDraftCreateTool(AgentTool):
    metadata = AgentToolMetadata(
        name="document_processing.medical_event_draft.create",
        description="Create a pending medical-event draft from structured user-provided information.",
        category="document",
        access_mode="draft",
        risk_level="high",
        required_permission_type="medical_events",
        required_permission_action="create",
        requires_confirmation=True,
        input_schema_name="MedicalEventDraftCreateInput",
        output_schema_name="MedicalEventDraftCreateOutput",
        safety_notes=(
            "Creates only a pending medical_event_draft; does not create formal medical_events.",
            "Does not call OCR or LLM and does not generate medical conclusions, prescription, dosage, or medication-change advice.",
            "Referenced documents or extraction results must match the target user and family scope.",
        ),
    )

    def validate_input(self, payload: dict[str, Any]) -> dict[str, Any]:
        draft_event_type = sanitize_optional_text(payload.get("draft_event_type"), max_length=32) or MedicalEventType.OTHER.value
        title = sanitize_optional_text(payload.get("draft_title", payload.get("title")), max_length=120)
        summary = sanitize_optional_text(payload.get("summary") or payload.get("extracted_text_preview"), max_length=3000)
        if not title and not summary and not payload.get("draft_json") and not payload.get("extraction_result_id"):
            raise ValueError("draft_title, summary, draft_json, or extraction_result_id is required")
        draft_json = _medical_event_draft_json(
            sanitize_optional_json(payload.get("draft_json"), max_string_length=1000, max_total_length=10000),
            draft_event_type=draft_event_type,
            title=title,
            summary=summary,
            event_date=sanitize_optional_text(payload.get("event_date"), max_length=32),
            hospital_or_org=sanitize_optional_text(payload.get("hospital_or_org"), max_length=120),
            department=sanitize_optional_text(payload.get("department"), max_length=120),
            structured_hints=sanitize_optional_json(payload.get("structured_hints"), max_string_length=255, max_total_length=2000),
        )
        return {
            "draft_event_type": draft_event_type,
            "draft_title": title,
            "draft_json": draft_json,
            "source_document_id": _optional_uuid(payload.get("source_document_id")),
            "extraction_result_id": _optional_uuid(payload.get("extraction_result_id")),
            "missing_fields": _optional_string_list(payload.get("missing_fields")),
            "safety_flags": _optional_string_list(payload.get("safety_flags")),
        }

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        db = _require_db(payload)
        target_user_id = payload["_target_user_id"]
        family_id = payload.get("_family_id")
        source_document_id = payload.get("source_document_id")
        extraction_result_id = payload.get("extraction_result_id")
        if source_document_id is not None:
            document = document_service.get_document(db, source_document_id)
            _ensure_same_scope(document, target_user_id=target_user_id, family_id=family_id)
        if extraction_result_id is not None:
            result = document_processing_service.get_extraction_result(db, extraction_result_id)
            _ensure_same_scope(result, target_user_id=target_user_id, family_id=family_id)
            if source_document_id is not None and result.document_id != source_document_id:
                raise ValueError("referenced extraction result does not belong to the source document")

        draft = document_processing_service.create_medical_event_draft(
            db,
            user_id=target_user_id,
            family_id=family_id,
            created_by_user_id=payload["_actor_user_id"],
            draft_event_type=payload["draft_event_type"],
            draft_title=payload.get("draft_title"),
            draft_json=payload["draft_json"],
            source_document_id=source_document_id,
            extraction_result_id=extraction_result_id,
            missing_fields=payload.get("missing_fields"),
            safety_flags=payload.get("safety_flags"),
        )
        return {
            "draft_id": str(draft.id),
            "status": getattr(draft.status, "value", draft.status),
            "safe_summary": "Pending medical event draft created from confirmed user input. It is not a formal medical event.",
        }


class DocumentsQueryTool(AgentTool):
    metadata = AgentToolMetadata(
        name="documents.query",
        description="Read safe medical document metadata summaries for the target user.",
        category="document",
        access_mode="read",
        risk_level="medium",
        required_permission_type="documents",
        required_permission_action="view",
        requires_confirmation=False,
        input_schema_name="DocumentsQueryInput",
        output_schema_name="DocumentsQueryOutput",
        safety_notes=("Never returns file_path, raw OCR, or full extracted text.",),
    )

    def validate_input(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"limit": _bounded_int(payload.get("limit", 10), field_name="limit", minimum=1, maximum=50)}

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        db = _require_db(payload)
        documents = document_service.list_user_documents(
            db,
            user_id=payload["_target_user_id"],
            family_id=payload.get("_family_id"),
        )[: payload["limit"]]
        return {
            "status": "ok",
            "source": "system_records",
            "empty": len(documents) == 0,
            "count": len(documents),
            "coverage_note": "Document metadata only; file paths and raw extracted text are omitted.",
            "items": [_document_summary(document) for document in documents],
        }


def _document_summary(document) -> dict[str, Any]:
    return {
        "id": str(document.id),
        "title": document.title,
        "document_type": getattr(document.document_type, "value", document.document_type),
        "file_name": document.file_name,
        "document_date": document.document_date,
        "ai_extract_status": getattr(document.ai_extract_status, "value", document.ai_extract_status),
        "visibility": getattr(document.visibility, "value", document.visibility),
    }


def _bounded_int(value: Any, *, field_name: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer") from exc
    if number < minimum or number > maximum:
        raise ValueError(f"{field_name} must be between {minimum} and {maximum}")
    return number


def _medical_event_draft_json(
    value: Any,
    *,
    draft_event_type: str,
    title: str | None,
    summary: str | None,
    event_date: str | None,
    hospital_or_org: str | None,
    department: str | None,
    structured_hints: dict[str, Any] | None,
) -> dict[str, Any]:
    if value is None:
        event_payload: dict[str, Any] = {"event_type": draft_event_type}
        if title:
            event_payload["title"] = title
        if summary:
            event_payload["summary"] = summary
        if event_date:
            _validate_iso_date(event_date)
            event_payload["event_date"] = event_date
        if hospital_or_org:
            event_payload["hospital_or_org"] = hospital_or_org
        if department:
            event_payload["department"] = department
        result = {"medical_event": event_payload, "source": "agent_tool"}
        if structured_hints:
            result["structured_hints"] = structured_hints
        return result
    if not isinstance(value, dict):
        raise ValueError("draft_json must be a dict")
    value.setdefault("source", "agent_tool")
    value.pop("diagnosis_text", None)
    value.pop("doctor_advice", None)
    value.pop("medications", None)
    nested = value.get("medical_event")
    if isinstance(nested, dict):
        nested.pop("diagnosis_text", None)
        nested.pop("doctor_advice", None)
        nested.pop("medications", None)
    return value


def _validate_iso_date(value: str) -> None:
    date.fromisoformat(value)


def _optional_uuid(value: Any) -> UUID | None:
    if value is None or value == "":
        return None
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def _optional_string_list(value: Any) -> list[str] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError("value must be a list")
    return [sanitize_required_text(item, max_length=120) for item in value]


def _ensure_same_scope(entity: Any, *, target_user_id: UUID, family_id: UUID | None) -> None:
    if entity.user_id != target_user_id:
        raise ValueError("referenced resource is not available for this target user")
    entity_family_id = getattr(entity, "family_id", None)
    if entity_family_id != family_id:
        raise ValueError("referenced resource is not available for this family context")


def _require_db(payload: dict[str, Any]) -> Session:
    db = payload.get("_db")
    if not isinstance(db, Session):
        raise ValueError("tool execution context is missing database session")
    return db

from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent.models import AgentTrace
from app.modules.alerts.models import Alert
from app.modules.document_center.models import MedicalDocument
from app.modules.document_processing.models import DocumentExtractionResult, MedicalEventDraft
from app.modules.health_data.models import BloodPressureRecord
from app.modules.health_profile.models import HealthProfile
from app.modules.health_record.models import SymptomRecord
from app.modules.medical_timeline.models import MedicalEvent
from app.modules.reports.models import DailyReport
from app.rag.schemas import RagIndexRecord, RagSourceType
from app.rag.source_policy import permission_for_source_type, safe_metadata, safe_text


def build_internal_rag_records(
    db: Session,
    *,
    target_user_id: UUID,
    family_id: UUID | None,
    source_types: Iterable[RagSourceType],
    limit_per_type: int = 30,
) -> tuple[RagIndexRecord, ...]:
    source_set = set(source_types)
    records: list[RagIndexRecord] = []
    if RagSourceType.HEALTH_PROFILE_SUMMARY in source_set:
        records.extend(_health_profile_records(db, target_user_id=target_user_id, family_id=family_id))
    if RagSourceType.BLOOD_PRESSURE_SUMMARY in source_set:
        records.extend(_blood_pressure_records(db, target_user_id=target_user_id, family_id=family_id, limit=limit_per_type))
    if RagSourceType.SYMPTOM_RECORD_SUMMARY in source_set:
        records.extend(_symptom_records(db, target_user_id=target_user_id, family_id=family_id, limit=limit_per_type))
    if RagSourceType.MEDICAL_EVENT_SUMMARY in source_set:
        records.extend(_medical_event_records(db, target_user_id=target_user_id, family_id=family_id, limit=limit_per_type))
    if RagSourceType.MEDICAL_EVENT_DRAFT_SUMMARY in source_set:
        records.extend(_medical_event_draft_records(db, target_user_id=target_user_id, family_id=family_id, limit=limit_per_type))
    if RagSourceType.MEDICAL_DOCUMENT_METADATA in source_set:
        records.extend(_document_metadata_records(db, target_user_id=target_user_id, family_id=family_id, limit=limit_per_type))
    if RagSourceType.DOCUMENT_EXTRACTION_PREVIEW in source_set or RagSourceType.OCR_EXTRACTION_PREVIEW in source_set:
        records.extend(_document_extraction_records(db, target_user_id=target_user_id, family_id=family_id, limit=limit_per_type))
    if RagSourceType.DAILY_REPORT_SUMMARY in source_set:
        records.extend(_daily_report_records(db, target_user_id=target_user_id, family_id=family_id, limit=limit_per_type))
    if RagSourceType.ALERT_SUMMARY in source_set:
        records.extend(_alert_records(db, target_user_id=target_user_id, family_id=family_id, limit=limit_per_type))
    if RagSourceType.AGENT_GENERATED_BRIEF_SUMMARY in source_set:
        records.extend(_agent_brief_records(db, target_user_id=target_user_id, family_id=family_id, limit=limit_per_type))
    return tuple(records)


def _health_profile_records(db: Session, *, target_user_id: UUID, family_id: UUID | None) -> tuple[RagIndexRecord, ...]:
    profile = db.scalar(select(HealthProfile).where(HealthProfile.user_id == target_user_id))
    if profile is None:
        return ()
    summary = "; ".join(
        part
        for part in (
            safe_text(profile.health_goal, max_length=300),
            safe_text(profile.chronic_conditions_summary, max_length=300),
            safe_text(profile.allergy_summary, max_length=300),
            safe_text(profile.medication_summary, max_length=300),
        )
        if part
    )
    if not summary:
        return ()
    return (_record(profile, RagSourceType.HEALTH_PROFILE_SUMMARY, "Health profile summary", summary, family_id=family_id),)


def _blood_pressure_records(db: Session, *, target_user_id: UUID, family_id: UUID | None, limit: int) -> tuple[RagIndexRecord, ...]:
    rows = db.scalars(
        select(BloodPressureRecord)
        .where(BloodPressureRecord.user_id == target_user_id)
        .order_by(BloodPressureRecord.measured_at.desc())
        .limit(limit)
    )
    return tuple(
        _record(
            row,
            RagSourceType.BLOOD_PRESSURE_SUMMARY,
            "Blood pressure record",
            f"Blood pressure values recorded at {row.measured_at}: systolic={row.systolic}, diastolic={row.diastolic}, pulse={row.pulse or 'not recorded'}. This is a recorded fact, not a diagnosis.",
            family_id=family_id,
            source_created_at=row.measured_at,
        )
        for row in rows
    )


def _symptom_records(db: Session, *, target_user_id: UUID, family_id: UUID | None, limit: int) -> tuple[RagIndexRecord, ...]:
    rows = db.scalars(
        select(SymptomRecord)
        .where(_family_user_filter(SymptomRecord, target_user_id, family_id))
        .order_by(SymptomRecord.created_at.desc())
        .limit(limit)
    )
    records = []
    for row in rows:
        summary = "; ".join(
            part
            for part in (
                safe_text(row.symptom_name, max_length=120),
                safe_text(row.body_part, max_length=120),
                safe_text(row.duration_text, max_length=120),
                safe_text(row.ai_summary, max_length=400),
            )
            if part
        )
        if summary:
            records.append(_record(row, RagSourceType.SYMPTOM_RECORD_SUMMARY, "Symptom record summary", summary, family_id=row.family_id))
    return tuple(records)


def _medical_event_records(db: Session, *, target_user_id: UUID, family_id: UUID | None, limit: int) -> tuple[RagIndexRecord, ...]:
    rows = db.scalars(
        select(MedicalEvent)
        .where(_family_user_filter(MedicalEvent, target_user_id, family_id))
        .order_by(MedicalEvent.created_at.desc())
        .limit(limit)
    )
    records = []
    for row in rows:
        summary = "; ".join(
            part
            for part in (
                safe_text(row.title, max_length=160),
                safe_text(row.event_date_text or row.event_date, max_length=80),
                safe_text(row.hospital_or_org, max_length=120),
                safe_text(row.department, max_length=120),
                safe_text(row.summary, max_length=500) if hasattr(row, "summary") else "",
            )
            if part
        )
        if summary:
            records.append(_record(row, RagSourceType.MEDICAL_EVENT_SUMMARY, "Medical event summary", summary, family_id=row.family_id))
    return tuple(records)


def _medical_event_draft_records(db: Session, *, target_user_id: UUID, family_id: UUID | None, limit: int) -> tuple[RagIndexRecord, ...]:
    rows = db.scalars(
        select(MedicalEventDraft)
        .where(_family_user_filter(MedicalEventDraft, target_user_id, family_id))
        .order_by(MedicalEventDraft.created_at.desc())
        .limit(limit)
    )
    records = []
    for row in rows:
        summary = "; ".join(
            part
            for part in (
                safe_text(row.draft_title, max_length=160),
                safe_text(row.draft_json, max_length=600),
                safe_text(row.status.value if hasattr(row.status, "value") else row.status, max_length=80),
            )
            if part
        )
        if summary:
            records.append(_record(row, RagSourceType.MEDICAL_EVENT_DRAFT_SUMMARY, "Medical event draft summary", summary, family_id=row.family_id))
    return tuple(records)


def _document_metadata_records(db: Session, *, target_user_id: UUID, family_id: UUID | None, limit: int) -> tuple[RagIndexRecord, ...]:
    rows = db.scalars(
        select(MedicalDocument)
        .where(_family_user_filter(MedicalDocument, target_user_id, family_id))
        .order_by(MedicalDocument.created_at.desc())
        .limit(limit)
    )
    records = []
    for row in rows:
        summary = "; ".join(
            part
            for part in (
                safe_text(row.title, max_length=160),
                safe_text(row.document_type.value if hasattr(row.document_type, "value") else row.document_type, max_length=120),
                safe_text(row.document_date_text or row.document_date, max_length=80),
                safe_text(row.hospital_or_org, max_length=120),
                safe_text(row.description, max_length=300),
                safe_text(row.ai_summary, max_length=400),
            )
            if part
        )
        if summary:
            records.append(_record(row, RagSourceType.MEDICAL_DOCUMENT_METADATA, "Medical document metadata", summary, family_id=row.family_id))
    return tuple(records)


def _document_extraction_records(db: Session, *, target_user_id: UUID, family_id: UUID | None, limit: int) -> tuple[RagIndexRecord, ...]:
    rows = db.scalars(
        select(DocumentExtractionResult)
        .where(_family_user_filter(DocumentExtractionResult, target_user_id, family_id))
        .order_by(DocumentExtractionResult.created_at.desc())
        .limit(limit)
    )
    records = []
    for row in rows:
        summary = "; ".join(
            part
            for part in (
                safe_text(row.ai_summary, max_length=500),
                safe_text(row.key_findings, max_length=500),
                safe_text(row.safety_notes, max_length=300),
            )
            if part
        )
        if summary:
            records.append(_record(row, RagSourceType.DOCUMENT_EXTRACTION_PREVIEW, "Document extraction preview", summary, family_id=row.family_id))
    return tuple(records)


def _daily_report_records(db: Session, *, target_user_id: UUID, family_id: UUID | None, limit: int) -> tuple[RagIndexRecord, ...]:
    rows = db.scalars(
        select(DailyReport)
        .where(_family_user_filter(DailyReport, target_user_id, family_id))
        .order_by(DailyReport.created_at.desc())
        .limit(limit)
    )
    records = []
    for row in rows:
        summary = "; ".join(
            part
            for part in (
                safe_text(row.summary_text, max_length=500),
                safe_text(row.highlights, max_length=400),
                safe_text(row.concerns, max_length=400),
                safe_text(row.suggestions, max_length=400),
            )
            if part
        )
        if summary:
            records.append(_record(row, RagSourceType.DAILY_REPORT_SUMMARY, "Daily report summary", summary, family_id=row.family_id))
    return tuple(records)


def _alert_records(db: Session, *, target_user_id: UUID, family_id: UUID | None, limit: int) -> tuple[RagIndexRecord, ...]:
    rows = db.scalars(
        select(Alert)
        .where(_family_user_filter(Alert, target_user_id, family_id))
        .order_by(Alert.created_at.desc())
        .limit(limit)
    )
    records = []
    for row in rows:
        summary = "; ".join(
            part
            for part in (
                safe_text(row.title, max_length=160),
                safe_text(row.message, max_length=300),
                safe_text(row.suggested_action, max_length=200),
                safe_text(row.trigger_reason, max_length=200),
            )
            if part
        )
        if summary:
            records.append(_record(row, RagSourceType.ALERT_SUMMARY, "Alert summary", summary, family_id=row.family_id))
    return tuple(records)


def _agent_brief_records(db: Session, *, target_user_id: UUID, family_id: UUID | None, limit: int) -> tuple[RagIndexRecord, ...]:
    rows = db.scalars(
        select(AgentTrace)
        .where(AgentTrace.target_user_id == target_user_id)
        .order_by(AgentTrace.started_at.desc())
        .limit(limit)
    )
    records = []
    for row in rows:
        summary = safe_text(row.final_output_summary, max_length=600)
        if summary:
            records.append(
                RagIndexRecord(
                    record_id=f"{RagSourceType.AGENT_GENERATED_BRIEF_SUMMARY.value}:{row.id}",
                    source_type=RagSourceType.AGENT_GENERATED_BRIEF_SUMMARY,
                    source_id=row.id,
                    owner_user_id=target_user_id,
                    target_user_id=target_user_id,
                    family_id=family_id,
                    title="Agent generated brief summary",
                    summary_text=summary,
                    safe_excerpt=safe_text(summary, max_length=300),
                    permission_type=permission_for_source_type(RagSourceType.AGENT_GENERATED_BRIEF_SUMMARY)[0],
                    source_created_at=row.started_at,
                    metadata_safe=safe_metadata({"workflow": row.workflow_name.value, "status": row.status.value}),
                )
            )
    return tuple(records)


def _record(
    row,
    source_type: RagSourceType,
    title: str,
    summary: str,
    *,
    family_id: UUID | None,
    source_created_at=None,
) -> RagIndexRecord:
    permission_type, action = permission_for_source_type(source_type)
    row_family_id = getattr(row, "family_id", None)
    return RagIndexRecord(
        record_id=f"{source_type.value}:{row.id}",
        source_type=source_type,
        source_id=row.id,
        owner_user_id=row.user_id,
        target_user_id=row.user_id,
        family_id=row_family_id if row_family_id is not None else family_id,
        title=title,
        summary_text=summary,
        safe_excerpt=safe_text(summary, max_length=300),
        permission_type=permission_type,
        permission_action=action,
        source_created_at=source_created_at or getattr(row, "created_at", None),
        metadata_safe=safe_metadata({"created_at": getattr(row, "created_at", None)}),
    )


def _family_user_filter(model, target_user_id: UUID, family_id: UUID | None):
    expression = model.user_id == target_user_id
    if family_id is not None and hasattr(model, "family_id"):
        expression = expression & (model.family_id == family_id)
    return expression

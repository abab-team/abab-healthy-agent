from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MedicalEventDraftConfirmation:
    draft_id: str
    medical_event_id: str
    source_document_id: str | None
    status: str

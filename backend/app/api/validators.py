from __future__ import annotations

from typing import Annotated, Any

from pydantic import BeforeValidator, ConfigDict, Field

from app.api.sanitizers import (
    sanitize_file_path,
    sanitize_optional_json,
    sanitize_optional_text,
    sanitize_required_json,
    sanitize_required_text,
)


STRICT_MODEL_CONFIG = ConfigDict(extra="forbid")


def optional_text(max_length: int):
    return BeforeValidator(lambda value: sanitize_optional_text(value, max_length=max_length))


def required_text(max_length: int):
    return BeforeValidator(lambda value: sanitize_required_text(value, max_length=max_length))


def optional_json(max_string_length: int = 1000, max_total_length: int = 10000):
    return BeforeValidator(
        lambda value: sanitize_optional_json(value, max_string_length=max_string_length, max_total_length=max_total_length)
    )


def required_json(max_string_length: int = 1000, max_total_length: int = 10000):
    return BeforeValidator(
        lambda value: sanitize_required_json(value, max_string_length=max_string_length, max_total_length=max_total_length)
    )


Nickname = Annotated[str | None, optional_text(64)]
DisplayName = Annotated[str | None, optional_text(64)]
RequiredDisplayName = Annotated[str, required_text(64), Field(min_length=1, max_length=64)]
RelationshipLabel = Annotated[str | None, optional_text(64)]
RequiredRelationshipLabel = Annotated[str, required_text(64), Field(min_length=1, max_length=64)]
Name = Annotated[str, required_text(120), Field(min_length=1, max_length=120)]
OptionalName = Annotated[str | None, optional_text(120)]
Title = Annotated[str, required_text(120), Field(min_length=1, max_length=120)]
OptionalTitle = Annotated[str | None, optional_text(120)]
Email = Annotated[str | None, optional_text(254)]
Phone = Annotated[str | None, optional_text(64)]
RawText = Annotated[str, required_text(2000), Field(min_length=1, max_length=2000)]
OptionalRawText = Annotated[str | None, optional_text(2000)]
SummaryText = Annotated[str | None, optional_text(3000)]
DoctorAdvice = Annotated[str | None, optional_text(3000)]
Description = Annotated[str | None, optional_text(1000)]
Note = Annotated[str | None, optional_text(1000)]
Reason = Annotated[str | None, optional_text(1000)]
SuggestedAction = Annotated[str | None, optional_text(1000)]
TriggerReason = Annotated[str | None, optional_text(1000)]
RawExtractedText = Annotated[str | None, optional_text(10000)]
FileName = Annotated[str, required_text(255), Field(min_length=1, max_length=255)]
FilePath = Annotated[str, BeforeValidator(lambda value: sanitize_file_path(value, max_length=512)), Field(min_length=1, max_length=512)]
SourceDetail = Annotated[str | None, optional_text(255)]
HospitalOrOrg = Annotated[str | None, optional_text(120)]
Department = Annotated[str | None, optional_text(120)]
ShortText = Annotated[str | None, optional_text(255)]
RequiredShortText = Annotated[str, required_text(255), Field(min_length=1, max_length=255)]
RequiredAlertText = Annotated[str, required_text(1000), Field(min_length=1, max_length=1000)]
JsonDict = Annotated[dict | None, optional_json()]
RequiredJsonDict = Annotated[dict, required_json()]
JsonList = Annotated[list[dict] | None, optional_json()]
StringList = Annotated[list[str] | None, optional_json(max_string_length=255, max_total_length=5000)]
AnyJson = Annotated[Any, required_json()]

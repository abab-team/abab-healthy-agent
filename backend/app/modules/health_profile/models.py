from __future__ import annotations

from datetime import date
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Date, Enum, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.health_profile.enums import BloodType
from app.modules.identity.enums import Gender


def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [item.value for item in enum_cls]


class HealthProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "health_profiles"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    height_cm: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    gender: Mapped[Gender | None] = mapped_column(
        Enum(
            Gender,
            values_callable=enum_values,
            native_enum=False,
            length=32,
        ),
        nullable=True,
    )
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    blood_type: Mapped[BloodType | None] = mapped_column(
        Enum(
            BloodType,
            values_callable=enum_values,
            native_enum=False,
            length=16,
        ),
        nullable=True,
    )
    health_goal: Mapped[str | None] = mapped_column(String(500), nullable=True)
    chronic_conditions_summary: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    allergy_summary: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    medication_summary: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    __table_args__ = (Index("ix_health_profiles_user_id", "user_id"),)

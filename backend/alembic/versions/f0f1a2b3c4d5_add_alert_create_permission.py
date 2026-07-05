"""add_alert_create_permission

Revision ID: f0f1a2b3c4d5
Revises: ae420c0ea01f
Create Date: 2026-07-05 18:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f0f1a2b3c4d5"
down_revision: str | None = "ae420c0ea01f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "member_share_permissions",
        sa.Column("can_create_alerts", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    if op.get_bind().dialect.name != "sqlite":
        op.alter_column("member_share_permissions", "can_create_alerts", server_default=None)


def downgrade() -> None:
    op.drop_column("member_share_permissions", "can_create_alerts")

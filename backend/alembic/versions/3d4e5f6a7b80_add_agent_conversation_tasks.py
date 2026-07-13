"""add agent conversation tasks

Revision ID: 3d4e5f6a7b80
Revises: 2c3d4e5f6a70
Create Date: 2026-07-13 10:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "3d4e5f6a7b80"
down_revision: str | None = "2c3d4e5f6a70"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_conversation_tasks",
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("task_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("task_payload", sa.JSON(), nullable=True),
        sa.Column("missing_fields", sa.JSON(), nullable=True),
        sa.Column("target_member", sa.String(length=64), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["agent_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_conversation_tasks_session_id", "agent_conversation_tasks", ["session_id"], unique=False)
    op.create_index("ix_agent_conversation_tasks_status", "agent_conversation_tasks", ["status"], unique=False)
    op.create_index("ix_agent_conversation_tasks_expires_at", "agent_conversation_tasks", ["expires_at"], unique=False)
    op.create_index(
        "ix_agent_conversation_tasks_session_status",
        "agent_conversation_tasks",
        ["session_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_agent_conversation_tasks_session_status", table_name="agent_conversation_tasks")
    op.drop_index("ix_agent_conversation_tasks_expires_at", table_name="agent_conversation_tasks")
    op.drop_index("ix_agent_conversation_tasks_status", table_name="agent_conversation_tasks")
    op.drop_index("ix_agent_conversation_tasks_session_id", table_name="agent_conversation_tasks")
    op.drop_table("agent_conversation_tasks")

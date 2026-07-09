"""add_agent_memory_tables

Revision ID: 1b2c3d4e5f60
Revises: f0f1a2b3c4d5
Create Date: 2026-07-09 19:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "1b2c3d4e5f60"
down_revision: str | None = "f0f1a2b3c4d5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_sessions",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("family_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=120), nullable=True),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_sessions_created_at", "agent_sessions", ["created_at"], unique=False)
    op.create_index("ix_agent_sessions_family_id", "agent_sessions", ["family_id"], unique=False)
    op.create_index("ix_agent_sessions_last_active_at", "agent_sessions", ["last_active_at"], unique=False)
    op.create_index("ix_agent_sessions_user_id", "agent_sessions", ["user_id"], unique=False)

    op.create_table(
        "agent_messages",
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content_summary", sa.Text(), nullable=False),
        sa.Column("intent", sa.String(length=100), nullable=True),
        sa.Column("target_user_id", sa.Uuid(), nullable=True),
        sa.Column("member_label", sa.String(length=64), nullable=True),
        sa.Column("member_scope", sa.String(length=32), nullable=True),
        sa.Column("metric_type", sa.String(length=64), nullable=True),
        sa.Column("time_range_label", sa.String(length=64), nullable=True),
        sa.Column("time_range_days", sa.Integer(), nullable=True),
        sa.Column("tool_name", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["agent_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_messages_created_at", "agent_messages", ["created_at"], unique=False)
    op.create_index("ix_agent_messages_intent", "agent_messages", ["intent"], unique=False)
    op.create_index("ix_agent_messages_metric_type", "agent_messages", ["metric_type"], unique=False)
    op.create_index("ix_agent_messages_role", "agent_messages", ["role"], unique=False)
    op.create_index("ix_agent_messages_session_id", "agent_messages", ["session_id"], unique=False)
    op.create_index("ix_agent_messages_target_user_id", "agent_messages", ["target_user_id"], unique=False)

    op.create_table(
        "agent_memory_items",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("family_id", sa.Uuid(), nullable=True),
        sa.Column("memory_type", sa.String(length=64), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("structured_data_json", sa.JSON(), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("is_user_editable", sa.Boolean(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_memory_items_created_at", "agent_memory_items", ["created_at"], unique=False)
    op.create_index("ix_agent_memory_items_deleted_at", "agent_memory_items", ["deleted_at"], unique=False)
    op.create_index("ix_agent_memory_items_expires_at", "agent_memory_items", ["expires_at"], unique=False)
    op.create_index("ix_agent_memory_items_family_id", "agent_memory_items", ["family_id"], unique=False)
    op.create_index("ix_agent_memory_items_is_user_editable", "agent_memory_items", ["is_user_editable"], unique=False)
    op.create_index("ix_agent_memory_items_memory_type", "agent_memory_items", ["memory_type"], unique=False)
    op.create_index("ix_agent_memory_items_source", "agent_memory_items", ["source"], unique=False)
    op.create_index("ix_agent_memory_items_user_id", "agent_memory_items", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_agent_memory_items_user_id", table_name="agent_memory_items")
    op.drop_index("ix_agent_memory_items_source", table_name="agent_memory_items")
    op.drop_index("ix_agent_memory_items_memory_type", table_name="agent_memory_items")
    op.drop_index("ix_agent_memory_items_is_user_editable", table_name="agent_memory_items")
    op.drop_index("ix_agent_memory_items_family_id", table_name="agent_memory_items")
    op.drop_index("ix_agent_memory_items_expires_at", table_name="agent_memory_items")
    op.drop_index("ix_agent_memory_items_deleted_at", table_name="agent_memory_items")
    op.drop_index("ix_agent_memory_items_created_at", table_name="agent_memory_items")
    op.drop_table("agent_memory_items")

    op.drop_index("ix_agent_messages_target_user_id", table_name="agent_messages")
    op.drop_index("ix_agent_messages_session_id", table_name="agent_messages")
    op.drop_index("ix_agent_messages_role", table_name="agent_messages")
    op.drop_index("ix_agent_messages_metric_type", table_name="agent_messages")
    op.drop_index("ix_agent_messages_intent", table_name="agent_messages")
    op.drop_index("ix_agent_messages_created_at", table_name="agent_messages")
    op.drop_table("agent_messages")

    op.drop_index("ix_agent_sessions_user_id", table_name="agent_sessions")
    op.drop_index("ix_agent_sessions_last_active_at", table_name="agent_sessions")
    op.drop_index("ix_agent_sessions_family_id", table_name="agent_sessions")
    op.drop_index("ix_agent_sessions_created_at", table_name="agent_sessions")
    op.drop_table("agent_sessions")

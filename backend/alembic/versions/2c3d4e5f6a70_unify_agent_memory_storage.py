"""unify agent memory storage

Revision ID: 2c3d4e5f6a70
Revises: 1b2c3d4e5f60
Create Date: 2026-07-09 00:00:00.000000
"""

from __future__ import annotations

from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text


revision = "2c3d4e5f6a70"
down_revision = "1b2c3d4e5f60"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "agent_memory_items" not in inspector.get_table_names():
        return

    rows = bind.execute(
        text(
            """
            SELECT id, user_id, family_id, memory_type, content, confidence, source,
                   expires_at, deleted_at, created_at, updated_at
            FROM agent_memory_items
            """
        )
    ).mappings()
    for row in rows:
        memory_type = _memory_type(row["memory_type"])
        status = "deleted" if row["deleted_at"] is not None else "active"
        exists = bind.execute(
            text(
                """
                SELECT id
                FROM agent_memories
                WHERE user_id = :user_id
                  AND memory_type = :memory_type
                  AND content = :content
                  AND status = :status
                LIMIT 1
                """
            ),
            {
                "user_id": row["user_id"],
                "memory_type": memory_type,
                "content": row["content"],
                "status": status,
            },
        ).first()
        if exists is not None:
            continue
        bind.execute(
            text(
                """
                INSERT INTO agent_memories (
                    id, user_id, family_id, target_user_id, memory_type, content,
                    source, source_entity_type, source_entity_id, confidence_level,
                    visibility, status, last_used_at, expires_at, created_at, updated_at
                )
                VALUES (
                    :id, :user_id, :family_id, NULL, :memory_type, :content,
                    :source, NULL, NULL, :confidence_level,
                    :visibility, :status, NULL, :expires_at, :created_at, :updated_at
                )
                """
            ),
            {
                "id": str(uuid4()),
                "user_id": row["user_id"],
                "family_id": row["family_id"],
                "memory_type": memory_type,
                "content": row["content"],
                "source": _source(row["source"]),
                "confidence_level": _confidence_level(row["confidence"]),
                "visibility": "family_context" if row["family_id"] is not None else "private",
                "status": status,
                "expires_at": row["expires_at"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            },
        )

    _drop_agent_memory_items(inspector)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "agent_memory_items" in inspector.get_table_names():
        return
    op.create_table(
        "agent_memory_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("family_id", sa.Uuid(), nullable=True),
        sa.Column("memory_type", sa.String(length=64), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("structured_data_json", sa.JSON(), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("is_user_editable", sa.Boolean(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
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


def _drop_agent_memory_items(inspector) -> None:
    indexes = {index["name"] for index in inspector.get_indexes("agent_memory_items")}
    for index_name in (
        "ix_agent_memory_items_user_id",
        "ix_agent_memory_items_source",
        "ix_agent_memory_items_memory_type",
        "ix_agent_memory_items_is_user_editable",
        "ix_agent_memory_items_family_id",
        "ix_agent_memory_items_expires_at",
        "ix_agent_memory_items_deleted_at",
        "ix_agent_memory_items_created_at",
    ):
        if index_name in indexes:
            op.drop_index(index_name, table_name="agent_memory_items")
    op.drop_table("agent_memory_items")


def _memory_type(value: str | None) -> str:
    if value == "attention_focus":
        return "attention_focus"
    return "user_preference"


def _source(value: str | None) -> str:
    if value in {"user_input", "workflow", "system", "manual"}:
        return value
    if value == "user_confirmed_preference":
        return "user_input"
    return "system"


def _confidence_level(value: int | None) -> str:
    confidence = int(value or 0)
    if confidence >= 80:
        return "high"
    if confidence >= 50:
        return "medium"
    if confidence > 0:
        return "low"
    return "unknown"

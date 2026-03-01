"""Initial schema: CandidateStory, TWNGStoryRecord, AuditLog

Revision ID: 0001
Revises:
Create Date: 2026-02-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- candidate_stories ---
    op.create_table(
        "candidate_stories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("source_id", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("created_at_source", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("language", sa.Text(), nullable=True),
        sa.Column("prefilter_flags", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("story_score", sa.Double(), nullable=True),
        sa.Column("score_components", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("category_pred", sa.Text(), nullable=True),
        sa.Column("category_confidence", sa.Double(), nullable=True),
        sa.Column("entities", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("summary_draft", sa.Text(), nullable=True),
        sa.Column("tags_pred", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="new"),
        sa.Column("reviewer_notes", sa.Text(), nullable=True),
        sa.UniqueConstraint("source_type", "source_id", name="uq_candidate_source"),
    )
    op.create_index("ix_candidate_status", "candidate_stories", ["status"])
    op.create_index("ix_candidate_story_score", "candidate_stories", ["story_score"])
    op.create_index("ix_candidate_created_at_source", "candidate_stories", ["created_at_source"])

    # --- twng_story_records ---
    op.create_table(
        "twng_story_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidate_stories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("credit_text", sa.Text(), nullable=True),
        sa.Column("summary_final", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("language", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("visibility", sa.Text(), nullable=False, server_default="internal"),
        sa.Column("takedown_status", sa.Text(), nullable=False, server_default="active"),
    )

    # --- audit_logs ---
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("actor", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("target_type", sa.Text(), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("details", postgresql.JSONB(), nullable=False, server_default="{}"),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("twng_story_records")
    op.drop_table("candidate_stories")

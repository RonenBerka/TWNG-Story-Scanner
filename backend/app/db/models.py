"""SQLAlchemy models for TWNG Story Scanner."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Double,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class CandidateStory(Base):
    __tablename__ = "candidate_stories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_type = Column(Text, nullable=False)  # 'reddit' | 'web'
    source_id = Column(Text, nullable=False)  # reddit post id or url hash
    source_url = Column(Text, nullable=False)
    title = Column(Text, nullable=True)
    raw_text = Column(Text, nullable=True)  # TEMP retention; cleaned later
    excerpt = Column(Text, nullable=True)
    created_at_source = Column(DateTime(timezone=True), nullable=True)
    ingested_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    language = Column(Text, nullable=True)
    prefilter_flags = Column(JSONB, nullable=False, server_default="{}")
    story_score = Column(Double, nullable=True)
    score_components = Column(JSONB, nullable=False, server_default="{}")
    category_pred = Column(Text, nullable=True)
    category_confidence = Column(Double, nullable=True)
    entities = Column(JSONB, nullable=False, server_default="{}")
    summary_draft = Column(Text, nullable=True)
    tags_pred = Column(ARRAY(Text), nullable=True)
    status = Column(Text, nullable=False, server_default="new")  # new|reviewed|approved|rejected
    reviewer_notes = Column(Text, nullable=True)

    # Relationship to approved record
    record = relationship("TWNGStoryRecord", back_populates="candidate", uselist=False)

    __table_args__ = (
        UniqueConstraint("source_type", "source_id", name="uq_candidate_source"),
        Index("ix_candidate_status", "status"),
        Index("ix_candidate_story_score", "story_score"),
        Index("ix_candidate_created_at_source", "created_at_source"),
    )


class TWNGStoryRecord(Base):
    __tablename__ = "twng_story_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(
        UUID(as_uuid=True),
        ForeignKey("candidate_stories.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_url = Column(Text, nullable=False)
    source_type = Column(Text, nullable=False)
    credit_text = Column(Text, nullable=True)
    summary_final = Column(Text, nullable=False)
    category = Column(Text, nullable=True)
    tags = Column(ARRAY(Text), nullable=True)
    language = Column(Text, nullable=True)
    published_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    visibility = Column(
        Text, nullable=False, server_default="internal"
    )  # internal|public|private
    takedown_status = Column(
        Text, nullable=False, server_default="active"
    )  # active|removed

    candidate = relationship("CandidateStory", back_populates="record")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor = Column(Text, nullable=False)
    action = Column(Text, nullable=False)
    target_type = Column(Text, nullable=False)
    target_id = Column(UUID(as_uuid=True), nullable=True)
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    details = Column(JSONB, nullable=False, server_default="{}")

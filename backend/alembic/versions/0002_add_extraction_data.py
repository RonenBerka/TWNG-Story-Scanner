"""Add extraction_data JSONB column to twng_story_records.

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "twng_story_records",
        sa.Column("extraction_data", JSONB, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("twng_story_records", "extraction_data")

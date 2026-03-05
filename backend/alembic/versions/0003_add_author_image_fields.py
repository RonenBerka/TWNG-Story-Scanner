"""Add author_username, author_profile_url, image_urls to candidate_stories.

These fields support the TWNG export's owner_contact and image sections.

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "candidate_stories",
        sa.Column("author_username", sa.Text(), nullable=True),
    )
    op.add_column(
        "candidate_stories",
        sa.Column("author_profile_url", sa.Text(), nullable=True),
    )
    op.add_column(
        "candidate_stories",
        sa.Column("image_urls", ARRAY(sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("candidate_stories", "image_urls")
    op.drop_column("candidate_stories", "author_profile_url")
    op.drop_column("candidate_stories", "author_username")

"""audits.metadata for Addendum v1.1 (backlinks)

Adds the JSONB `metadata` column to `audits`. Build Doc §4.2 omitted it; the
v1.1 addendum stores backlink data in audits.metadata['backlinks'].

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-18
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE audits ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE audits DROP COLUMN IF EXISTS metadata")

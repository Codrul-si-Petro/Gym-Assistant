"""Create core schema

Revision ID: 001
Revises:
Create Date: 2026-01-21
"""

from collections.abc import Sequence

from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS core")


def downgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS core CASCADE")

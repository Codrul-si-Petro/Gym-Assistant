"""Create seeds schema for dbt seeds

Revision ID: 005
Revises: 004
Create Date: 2026-01-22
"""

from collections.abc import Sequence

from alembic import op

revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS seeds")


def downgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS seeds CASCADE")

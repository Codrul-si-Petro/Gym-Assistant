"""Drop unused auth schema

Revision ID: 004
Revises: 003
Create Date: 2026-01-22

Note: Auth tables are managed by Django in the public schema.
The auth schema was created in error and is no longer needed.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS auth CASCADE")


def downgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS auth")

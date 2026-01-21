"""Placeholder migration (auth tables managed by Django)

Revision ID: 002
Revises: 001
Create Date: 2026-01-21

Note: All auth tables are managed by Django in the public schema.
This migration is kept for revision chain continuity.
"""

from collections.abc import Sequence

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

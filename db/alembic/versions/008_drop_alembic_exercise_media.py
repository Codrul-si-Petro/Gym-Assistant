"""Drop legacy Alembic-owned exercise_media so dbt can manage the table

Revision ID: 008
Revises: 007
Create Date: 2026-06-16
"""

from collections.abc import Sequence

from alembic import op

revision: str = "008"
down_revision: str | None = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS core.exercise_media CASCADE")


def downgrade() -> None:
    pass

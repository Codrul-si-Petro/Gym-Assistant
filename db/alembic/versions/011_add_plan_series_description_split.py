"""Add description and workout_split to plan_series

Revision ID: 011
Revises: 010
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "011"
down_revision: str | None = "010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "plan_series",
        sa.Column("description", sa.Text(), nullable=True),
        schema="core",
    )
    op.add_column(
        "plan_series",
        sa.Column("workout_split", sa.Text(), nullable=True),
        schema="core",
    )


def downgrade() -> None:
    op.drop_column("plan_series", "workout_split", schema="core")
    op.drop_column("plan_series", "description", schema="core")

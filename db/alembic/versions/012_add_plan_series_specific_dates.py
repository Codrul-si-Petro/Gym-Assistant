"""Add specific_dates to plan_series for ad-hoc calendar date plans

Revision ID: 012
Revises: 011
Create Date: 2026-07-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "012"
down_revision: str | None = "011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "plan_series",
        sa.Column("specific_dates", sa.Text(), nullable=True),
        schema="core",
    )


def downgrade() -> None:
    op.drop_column("plan_series", "specific_dates", schema="core")

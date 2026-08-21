"""Drop duplicate user_id index on core.fact_workouts

Revision ID: 013
Revises: 012
Create Date: 2026-07-23

ix_fact_workout_user_id duplicates ix_core_fact_workouts_user_id (both single-column
on user_id). Keep the older ix_core_fact_workouts_user_id name.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "013"
down_revision: str | None = "012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS core.ix_fact_workout_user_id"))


def downgrade() -> None:
    op.create_index(
        "ix_fact_workout_user_id",
        "fact_workouts",
        ["user_id"],
        unique=False,
        schema="core",
    )

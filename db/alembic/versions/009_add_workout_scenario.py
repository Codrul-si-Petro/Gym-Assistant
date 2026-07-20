"""Add scenario column (actuals|plan) to fact_workouts

Revision ID: 009
Revises: 008
Create Date: 2026-07-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "009"
down_revision: str | None = "008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCENARIO_ENUM = sa.Enum("actuals", "plan", name="workout_scenario", schema="core")


def upgrade() -> None:
    SCENARIO_ENUM.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "fact_workouts",
        sa.Column(
            "scenario",
            SCENARIO_ENUM,
            server_default="actuals",
            nullable=False,
        ),
        schema="core",
    )
    op.create_index(
        "ix_fact_workout_user_scenario_date",
        "fact_workouts",
        ["user_id", "scenario", "date_id"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index("ix_fact_workout_user_scenario_date", table_name="fact_workouts", schema="core")
    op.drop_column("fact_workouts", "scenario", schema="core")
    SCENARIO_ENUM.drop(op.get_bind(), checkfirst=True)

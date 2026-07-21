"""Add plan_series table and plan_group_id on fact_workouts

Revision ID: 010
Revises: 009
Create Date: 2026-07-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "010"
down_revision: str | None = "009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Orphan enum left by a failed prior attempt of this revision (sa.Enum + create_table).
    op.execute(sa.text("DROP TYPE IF EXISTS core.plan_recurrence_type"))

    op.create_table(
        "plan_series",
        sa.Column("plan_series_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("recurrence_type", sa.Text(), nullable=False),
        sa.Column("weekdays", sa.Text(), nullable=True),
        sa.Column("interval_days", sa.SmallInteger(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("ta_created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("ta_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["public.authentication_user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("plan_series_id"),
        schema="core",
    )
    op.create_index("ix_plan_series_user_id", "plan_series", ["user_id"], unique=False, schema="core")
    op.add_column(
        "fact_workouts",
        sa.Column("plan_group_id", sa.Uuid(), nullable=True),
        schema="core",
    )
    op.create_index(
        "ix_fact_workout_plan_group_id",
        "fact_workouts",
        ["plan_group_id"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index("ix_fact_workout_plan_group_id", table_name="fact_workouts", schema="core")
    op.drop_column("fact_workouts", "plan_group_id", schema="core")
    op.drop_index("ix_plan_series_user_id", table_name="plan_series", schema="core")
    op.drop_table("plan_series", schema="core")

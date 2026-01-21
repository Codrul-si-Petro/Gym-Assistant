"""Create core schema tables

Revision ID: 003
Revises: 002
Create Date: 2026-01-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Calendar dimension table
    op.create_table(
        "dim_calendar",
        sa.Column("date_id", sa.Date(), nullable=False),
        sa.Column("week_day", sa.SmallInteger(), nullable=False),
        sa.Column("day_number_in_month", sa.SmallInteger(), nullable=False),
        sa.Column("day_name_in_week", sa.Text(), nullable=False),
        sa.Column("calendar_month_number", sa.SmallInteger(), nullable=False),
        sa.Column("calendar_month_name", sa.Text(), nullable=False),
        sa.Column("calendar_year", sa.SmallInteger(), nullable=False),
        sa.Column("is_weekend", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("date_id"),
        schema="core",
    )

    # Exercises dimension table
    op.create_table(
        "dim_exercises",
        sa.Column("exercise_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("exercise_name", sa.Text(), nullable=False),
        sa.Column("exercise_movement_type", sa.Text(), nullable=False),
        sa.Column("ta_created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("ta_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("exercise_id"),
        schema="core",
    )

    # Muscles dimension table
    op.create_table(
        "dim_muscles",
        sa.Column("muscle_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("muscle_name", sa.Text(), nullable=False),
        sa.Column("muscle_group", sa.Text(), nullable=False),
        sa.Column("ta_created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("ta_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("muscle_id"),
        schema="core",
    )

    # Equipment dimension table
    op.create_table(
        "dim_equipment",
        sa.Column("equipment_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("equipment_name", sa.Text(), nullable=False),
        sa.Column("equipment_description", sa.Text(), nullable=False),
        sa.Column("equipment_category", sa.Text(), nullable=False),
        sa.Column("ta_created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("ta_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("equipment_id"),
        schema="core",
    )

    # Attachments dimension table
    op.create_table(
        "dim_attachments",
        sa.Column("attachment_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("attachment_name", sa.Text(), nullable=False),
        sa.Column("attachment_description", sa.Text(), nullable=False),
        sa.Column("ta_created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("ta_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("attachment_id"),
        schema="core",
    )

    # Exercise-Muscle bridge table
    op.create_table(
        "exercise_muscle_bridge",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("muscle_id", sa.Integer(), nullable=False),
        sa.Column("muscle_role", sa.Text(), nullable=True),
        sa.Column("ta_created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("ta_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["exercise_id"], ["core.dim_exercises.exercise_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["muscle_id"], ["core.dim_muscles.muscle_id"], ondelete="CASCADE"),
        schema="core",
    )

    # Workouts fact table
    # Note: user_id references Django's authentication_user table in public schema
    op.create_table(
        "fact_workouts",
        sa.Column("workout_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("workout_number", sa.Integer(), nullable=False),
        sa.Column("date_id", sa.Date(), nullable=False),
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("set_number", sa.SmallInteger(), nullable=False),
        sa.Column("repetitions", sa.SmallInteger(), nullable=False),
        sa.Column("load", sa.Numeric(9, 2), nullable=False),
        sa.Column("unit", sa.Text(), server_default="KG", nullable=False),
        sa.Column("equipment_id", sa.Integer(), nullable=False),
        sa.Column("attachment_id", sa.Integer(), nullable=False),
        sa.Column("set_type", sa.Text(), server_default="Working set", nullable=False),
        sa.Column("comments", sa.Text(), server_default="N/A", nullable=False),
        sa.Column("workout_split", sa.Text(), nullable=False),
        sa.Column("ta_created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("ta_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("workout_id"),
        sa.ForeignKeyConstraint(["user_id"], ["public.authentication_user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["date_id"], ["core.dim_calendar.date_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["exercise_id"], ["core.dim_exercises.exercise_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["equipment_id"], ["core.dim_equipment.equipment_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["attachment_id"], ["core.dim_attachments.attachment_id"], ondelete="CASCADE"),
        schema="core",
    )
    op.create_index("ix_core_fact_workouts_user_id", "fact_workouts", ["user_id"], schema="core")
    op.create_index("ix_core_fact_workouts_date_id", "fact_workouts", ["date_id"], schema="core")


def downgrade() -> None:
    op.drop_index("ix_core_fact_workouts_date_id", "fact_workouts", schema="core")
    op.drop_index("ix_core_fact_workouts_user_id", "fact_workouts", schema="core")
    op.drop_table("fact_workouts", schema="core")
    op.drop_table("exercise_muscle_bridge", schema="core")
    op.drop_table("dim_attachments", schema="core")
    op.drop_table("dim_equipment", schema="core")
    op.drop_table("dim_muscles", schema="core")
    op.drop_table("dim_exercises", schema="core")
    op.drop_table("dim_calendar", schema="core")

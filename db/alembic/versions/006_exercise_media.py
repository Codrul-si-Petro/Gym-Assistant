"""Add exercise_media table for glossary YouTube links

Revision ID: 006
Revises: 1f20500a6eac
Create Date: 2026-06-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: str | None = "1f20500a6eac"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # dim_exercises is rebuilt by dbt without a DB-level PK/unique constraint, so we
    # store exercise_id as a logical reference only (no FK).
    op.create_table(
        "exercise_media",
        sa.Column("media_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("youtube_url", sa.Text(), nullable=False),
        sa.Column("display_title", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("ta_created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("ta_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("media_id"),
        sa.UniqueConstraint("exercise_id", name="uq_exercise_media_exercise_id"),
        schema="core",
    )
    op.create_index(
        "ix_exercise_media_exercise_id",
        "exercise_media",
        ["exercise_id"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index("ix_exercise_media_exercise_id", table_name="exercise_media", schema="core")
    op.drop_table("exercise_media", schema="core")

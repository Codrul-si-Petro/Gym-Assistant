"""Seed exercise_media rows for glossary demo videos

Revision ID: 007
Revises: 006
Create Date: 2026-06-12
"""

from collections.abc import Sequence

from alembic import op

revision: str = "007"
down_revision: str | None = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SEED_ROWS = [
    (
        1,
        "https://www.youtube.com/watch?v=IODxDxX7oi4",
        "Push-up demo",
        "Keep core tight and full range of motion.",
    ),
    (
        2,
        "https://www.youtube.com/watch?v=aclHkVaku9U",
        "Pull-up demo",
        "Use controlled tempo on the way down.",
    ),
    (
        11,
        "https://youtu.be/bm0_q9bR_HA",
        "Bentover row demo",
        "Keep a flat back and pull toward your lower chest.",
    ),
]


def upgrade() -> None:
    for exercise_id, youtube_url, display_title, notes in SEED_ROWS:
        op.execute(
            f"""
            INSERT INTO core.exercise_media (exercise_id, youtube_url, display_title, notes)
            VALUES ({exercise_id}, '{youtube_url}', '{display_title}', '{notes}')
            ON CONFLICT (exercise_id) DO UPDATE SET
                youtube_url = EXCLUDED.youtube_url,
                display_title = EXCLUDED.display_title,
                notes = EXCLUDED.notes,
                ta_updated_at = NOW()
            """
        )


def downgrade() -> None:
    op.execute("DELETE FROM core.exercise_media WHERE exercise_id IN (1, 2, 11)")

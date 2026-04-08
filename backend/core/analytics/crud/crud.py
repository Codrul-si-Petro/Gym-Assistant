"""
Some stuff I will need to update at some point
"""

from datetime import date
from pathlib import Path

from .common import execute_sql, get_dimension_hierarchies, rollup_exercise_total_volume

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def get_rest_days(user_id):
    query_file = SQL_DIR / "get_user_rest_days.sql"
    query = query_file.read_text()

    return execute_sql(
        query,
        {
            "user_id": user_id,
        },
    )


def get_favourite_exercises(user_id, start_date, end_date):
    query_file = SQL_DIR / "get_favourite_exercises.sql"
    query = query_file.read_text()

    return execute_sql(
        query,
        {
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date,
        },
    )


def get_total_volume(user_id: int, start_date: date, end_date: date, parent_id: int | None):
    query_file = SQL_DIR / "get_total_volume.sql"  # yeah
    query = query_file.read_text()

    volume_rows = execute_sql(
        query,
        {
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date,
        },
    )

    hierarchy_rows = get_dimension_hierarchies("exercise")

    volume_by_exercise_id = {row["exercise_id"]: row["total_volume_kg"] or 0 for row in volume_rows}

    return rollup_exercise_total_volume(hierarchy_rows, volume_by_exercise_id, parent_id)

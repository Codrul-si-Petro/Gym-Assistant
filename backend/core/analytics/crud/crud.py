"""
Some stuff I will need to update at some point
"""

from pathlib import Path

from django.db import connection

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def execute_sql(sql: str, params: dict) -> list[dict]:
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

    return [dict(zip(columns, row)) for row in rows]


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


def get_total_volume(user_id, start_date, end_date, parent_id):
    query_file = SQL_DIR / "get_total_volume.sql"  # yeah
    query = query_file.read_text()

    return execute_sql(
        query,
        {"user_id": user_id, "start_date": start_date, "end_date": end_date, "parent_id": parent_id},
    )

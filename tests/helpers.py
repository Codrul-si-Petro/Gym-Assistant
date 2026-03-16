import os

import psycopg2
import requests


def delete_test_user(username: str):
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    cur.execute("DELETE FROM authentication_user WHERE username = %s", (username,))
    conn.commit()
    cur.close()
    conn.close()


def get_test_user_id(username: str) -> int | None:
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    cur.execute("SELECT id FROM public.authentication_user WHERE username = %s", (username,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None


def get_first_exercise(conn=None) -> dict | None:
    own_conn = conn is None
    if own_conn:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    cur.execute("SELECT exercise_id, exercise_name FROM core.dim_exercises ORDER BY exercise_name LIMIT 1")
    row = cur.fetchone()
    cur.close()
    if own_conn:
        conn.close()
    if not row:
        return None
    return {"exercise_id": row[0], "exercise_name": row[1]}


def get_max_workout_number(user_id: int) -> int:
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    cur.execute(
        "SELECT COALESCE(MAX(workout_number), 0) FROM core.fact_workouts WHERE user_id = %s",
        (user_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else 0


def get_latest_workout_for_user(user_id: int) -> dict | None:
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    cur.execute(
        """
        SELECT workout_id, user_id, workout_number, date_id, exercise_id,
               set_number, repetitions, load, unit, workout_split
        FROM core.fact_workouts
        WHERE user_id = %s
        ORDER BY ta_created_at DESC NULLS LAST
        LIMIT 1
        """,
        (user_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return None
    return {
        "workout_id": row[0],
        "user_id": row[1],
        "workout_number": row[2],
        "date_id": row[3],
        "exercise_id": row[4],
        "set_number": row[5],
        "repetitions": row[6],
        "load": float(row[7]) if row[7] is not None else None,
        "unit": row[8],
        "workout_split": row[9],
    }


def delete_latest_workout_for_user(user_id: int) -> None:
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    cur.execute(
        """
        DELETE FROM core.fact_workouts
        WHERE workout_id = (
            SELECT workout_id FROM core.fact_workouts
            WHERE user_id = %s
            ORDER BY ta_created_at DESC NULLS LAST
            LIMIT 1
        )
        """,
        (user_id,),
    )
    conn.commit()
    cur.close()
    conn.close()


def create_test_user(backend_url: str, username: str, password: str, email: str = "e2e-workout-test@test.com"):
    """Create a test user via the signup API. Silently succeeds if user already exists."""
    resp = requests.post(
        f"{backend_url}/api/auth/signup/",
        json={
            "username": username,
            "email": email,
            "password1": password,
            "password2": password,
        },
    )
    if resp.status_code == 201:
        return resp.json()["id"]
    # User might already exist — try to look up their ID
    return get_test_user_id(username)

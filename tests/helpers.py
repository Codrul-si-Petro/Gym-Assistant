import logging
import os
from contextlib import contextmanager

import psycopg2
import requests


@contextmanager
def db_cursor():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    logging.info("We are now connected to the database!")
    try:
        with conn:
            with conn.cursor() as cur:
                yield cur
    finally:
        conn.close()  # close it regardless of what happens


def get_test_user_id(username: str) -> int | None:
    with db_cursor() as cur:
        cur.execute(
            "SELECT id FROM public.authentication_user WHERE username = %s",
            (username,),
        )
        row = cur.fetchone()
        return row[0] if row else None


def get_first_exercise() -> dict | None:
    with db_cursor() as cur:
        cur.execute("SELECT exercise_id, exercise_name FROM core.dim_exercises ORDER BY exercise_name LIMIT 1")
        row = cur.fetchone()
        if not row:
            return None
    return {"exercise_id": row[0], "exercise_name": row[1]}


def get_first_equipment() -> dict | None:
    with db_cursor() as cur:
        cur.execute("SELECT equipment_id, equipment_name FROM core.dim_equipment ORDER BY equipment_name LIMIT 1")
        row = cur.fetchone()
        if not row:
            return None
    return {"equipment_id": row[0], "equipment_name": row[1]}


def get_max_workout_number(user_id: int) -> int:
    with db_cursor() as cur:
        # use coalesce because if there is no workout logged we get 1 at least
        cur.execute(
            "SELECT COALESCE(MAX(workout_number), 0) FROM core.fact_workouts WHERE user_id = %s",
            (user_id,),
        )
        row = cur.fetchone()
    return row[0] if row else 0


def get_latest_workout_for_user(user_id: int) -> dict | None:
    with db_cursor() as cur:
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
    with db_cursor() as cur:
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


E2E_DASHBOARD_WORKOUT_SPLIT = "e2e-dashboard-synthetic"


def create_test_user(backend_url: str, username: str, password: str, email: str = "e2e-gigel-rekinu@yahoo.com"):
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


def get_first_attachment_id() -> int | None:
    with db_cursor() as cur:
        cur.execute(
            "SELECT attachment_id FROM core.dim_attachments ORDER BY attachment_id LIMIT 1"
        )  # honestly I should get rid of this or parameterise it
        row = cur.fetchone()
    return int(row[0]) if row else None


def cleanup_e2e_dashboard_synthetic_rows(username: str) -> None:
    """Remove dashboard e2e seed rows (by workout_split tag)."""
    uid = get_test_user_id(username)
    if uid is None:
        logging.info("Could not get user ID. Skipping clean up.")
        return

    with db_cursor() as cur:
        cur.execute(
            "DELETE FROM core.fact_workouts WHERE user_id = %s",
            (uid,),
        )


def seed_e2e_dashboard_synthetic_rows(username: str) -> bool:
    """
    Insert fact_workouts for the UI tester so dashboard APIs return data.
    """
    cleanup_e2e_dashboard_synthetic_rows(username)
    uid = get_test_user_id(username)

    with db_cursor() as cur:
        cur.execute("SELECT date_id FROM core.dim_calendar WHERE date_id = CURRENT_DATE LIMIT 1")
        row = cur.fetchone()
        if not row:
            cur.execute("SELECT MAX(date_id) FROM core.dim_calendar")
            row = cur.fetchone()
        if not row or row[0] is None:
            return False
        date_id = row[0]

        ex = get_first_exercise()
        eq = get_first_equipment()
        att_id = get_first_attachment_id()
        if not ex or not eq or att_id is None:
            return False

        leaf_for_drill = 16
        cur.execute(
            "SELECT 1 FROM core.dim_exercises WHERE exercise_id = %s AND exercise_parent_id IS NOT NULL",
            (leaf_for_drill,),
        )
        if not cur.fetchone():
            leaf_for_drill = ex["exercise_id"]

        cur.execute(
            "SELECT COALESCE(MAX(workout_number), 0) FROM core.fact_workouts WHERE user_id = %s",
            (uid,),
        )
        wn = int(cur.fetchone()[0]) + 1

        bench_id = 9
        batch = [
            (uid, wn, date_id, leaf_for_drill, 1, 10, 100, eq["equipment_id"], att_id),
            (uid, wn, date_id, leaf_for_drill, 2, 8, 100, eq["equipment_id"], att_id),
            (uid, wn, date_id, bench_id, 1, 5, 60, eq["equipment_id"], att_id),
        ]

        for r in batch:
            cur.execute(
                """
                INSERT INTO core.fact_workouts (
                    user_id, workout_number, date_id, exercise_id, set_number, repetitions, load, unit,
                    equipment_id, attachment_id, set_type, comments, workout_split, laterality
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'KG', %s, %s, 'Working set', 'N/A', %s, 'Bilateral')
                """,
                (*r, E2E_DASHBOARD_WORKOUT_SPLIT),
            )

    return True

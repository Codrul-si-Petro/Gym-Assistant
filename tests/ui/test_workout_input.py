# TODO: refactor this horrible duplicated shit and actually put these helper functions somewhere. this is horrible but it works for now


import os
from datetime import date

import psycopg2
import pytest
from playwright.sync_api import Page, expect

# Reuse same base URL and credentials as test_auth
BASE_URL = os.getenv("E2E_BASE_URL", "https://gym-assistant-2smv.onrender.com")


@pytest.fixture(scope="module")
def test_credentials() -> tuple[str, str]:
    """Get test credentials, fail if not set."""
    login = os.getenv("UI_TESTER_USERNAME", "")
    password = os.getenv("UI_TESTER_PASS", "")
    if not login or not password:
        pytest.skip("UI_TESTER_USERNAME and UI_TESTER_PASS must be set")
    return login, password


def get_test_user_id(username: str) -> int | None:
    """Return auth user id for username. Uses public.auth_user (Django default); use authentication_user if your AUTH_USER_MODEL table is different."""
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    cur.execute("SELECT id FROM public.authentication_user WHERE username = %s", (username,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None


def get_first_exercise_name() -> str:
    """Return one exercise name from core.dim_exercises for form fill."""
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    cur.execute("SELECT exercise_name FROM core.dim_exercises ORDER BY exercise_name LIMIT 1")
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        pytest.skip("No exercises in core.dim_exercises")
    return row[0]


def get_max_workout_number(user_id: int) -> int:
    """Return current max workout_number for user in core.fact_workouts."""
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


def delete_latest_workout_for_user(user_id: int) -> None:
    """Delete the most recently created workout row for the given user."""
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


def get_latest_workout_for_user(user_id: int) -> dict | None:
    """Return the most recently created workout row for the user, or None."""
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


def get_exercise_id_by_name(exercise_name: str) -> int | None:
    """Return exercise_id for the given exercise name."""
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    cur.execute(
        "SELECT exercise_id FROM core.dim_exercises WHERE exercise_name = %s",
        (exercise_name,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None


@pytest.mark.order(3)
def test_workout_form_submit_then_delete(
    page: Page,
    test_credentials: tuple[str, str],
):
    """Go to workout form, log in, submit a workout, assert success, then delete the record from DB."""
    username, password = test_credentials

    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL must be set for workout form test")

    user_id = get_test_user_id(username)
    if user_id is None:
        pytest.skip(f"Test user '{username}' not found in auth_user")

    next_workout_number = get_max_workout_number(user_id) + 1
    exercise_name = get_first_exercise_name()
    today = date.today().isoformat()

    # Login
    page.goto(f"{BASE_URL}/accounts/login/")
    page.wait_for_load_state("networkidle")
    page.fill('input[name="login"]', username)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    expect(page).to_have_url(f"{BASE_URL}/", timeout=10000)

    # Workout form
    page.goto(f"{BASE_URL}/workouts/")
    page.wait_for_load_state("networkidle")
    expect(page).to_have_url(f"{BASE_URL}/workouts/")

    # Form fields that are inside the form
    page.fill('input[name="exercise_name"]', exercise_name)
    page.fill('input[name="set_number"]', "1")
    page.fill('input[name="repetitions"]', "10")
    page.fill('input[name="load"]', "50")

    # Fields associated via form="workout-form" (top-right)
    page.fill('input[name="workout_number"]', str(next_workout_number))
    page.fill('input[name="date"]', today)
    page.fill('input[name="workout_split"]', "E2E test split")

    page.click('form#workout-form >> button[type="submit"]')
    page.wait_for_load_state("networkidle")

    # Assert success by checking the database
    expect(page).to_have_url(f"{BASE_URL}/workouts/")
    latest = get_latest_workout_for_user(user_id)
    assert latest is not None, "No workout row found in DB after submit"
    exercise_id = get_exercise_id_by_name(exercise_name)
    assert exercise_id is not None, f"Exercise '{exercise_name}' not found in dim_exercises"
    assert latest["user_id"] == user_id
    assert latest["workout_number"] == next_workout_number
    assert latest["date_id"].isoformat() == today
    assert latest["exercise_id"] == exercise_id
    assert latest["set_number"] == 1
    assert latest["repetitions"] == 10
    assert latest["load"] == 50.0
    assert latest["unit"] == "KG"
    assert latest["workout_split"] == "E2E test split"

    # Teardown: delete the record we just created
    delete_latest_workout_for_user(user_id)

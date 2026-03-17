import os
from datetime import date

import pytest
from playwright.sync_api import Page, expect

from tests.helpers import (
    create_test_user,
    delete_latest_workout_for_user,
    get_first_exercise,
    get_latest_workout_for_user,
    get_max_workout_number,
)


@pytest.mark.order(3)
def test_workout_form_submit_then_delete(
    page: Page,
    test_credentials: tuple[str, str],
    frontend_url: str,
    backend_url: str,
):
    username, password = test_credentials

    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL must be set for workout form test")

    user_id = create_test_user(backend_url, username, password)
    if user_id is None:
        pytest.skip(f"Could not create or find test user '{username}'")

    exercise = get_first_exercise()
    if exercise is None:
        pytest.skip("No exercises in core.dim_exercises")

    next_workout_number = get_max_workout_number(user_id) + 1
    today = date.today().isoformat()

    # Login via SPA
    page.goto(f"{frontend_url}/pages/auth/login.html")
    page.wait_for_load_state("networkidle")
    page.wait_for_selector("#exercises_list option", timeout=1000)
    page.fill("#username", username)
    page.fill("#password", password)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    expect(page).to_have_url(f"{frontend_url}/index.html", timeout=10000)

    # Navigate to SPA workout input page
    page.goto(f"{frontend_url}/pages/core/workouts_input.html")
    page.wait_for_load_state("networkidle")

    # Fill the form
    page.fill("#exercise_name", exercise["exercise_name"])
    page.fill("#set_number", "1")
    page.fill("#repetitions", "10")
    page.fill("#load", "50")
    page.fill("#workout_number", str(next_workout_number))
    page.fill("#date", today)
    page.fill("#workout_split", "E2E test split")

    # Submit — SPA form submits via fetch(), no page reload
    page.click("#submit-btn")

    # Wait for success message to appear
    msg = page.locator("#message")
    expect(msg).to_contain_text("Workout saved", timeout=10000)

    # Verify in database
    latest = get_latest_workout_for_user(user_id)
    assert latest is not None, "No workout row found in DB after submit"
    assert latest["user_id"] == user_id
    assert latest["workout_number"] == next_workout_number
    assert latest["date_id"].isoformat() == today
    assert latest["exercise_id"] == exercise["exercise_id"]
    assert latest["set_number"] == 1
    assert latest["repetitions"] == 10
    assert latest["load"] == 50.0
    assert latest["unit"] == "KG"
    assert latest["workout_split"] == "E2E test split"

    # Teardown
    delete_latest_workout_for_user(user_id)

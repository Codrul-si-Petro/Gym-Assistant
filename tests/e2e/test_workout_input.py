import os
from datetime import date

import pytest
from playwright.sync_api import Page, expect

from tests.helpers import (
    delete_latest_workout_for_user,
    get_first_equipment,
    get_first_exercise,
    get_latest_workout_for_user,
    get_max_workout_number,
)


@pytest.mark.order(3)
def test_workout_form_submit_then_delete(page: Page, ui_tester_session: tuple[str, str, int], frontend_url: str):
    username, password, user_id = ui_tester_session

    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL must be set for workout form test")

    exercise = get_first_exercise()
    if exercise is None:
        pytest.skip("No exercises in core.dim_exercises")

    equipment = get_first_equipment()
    if equipment is None:
        pytest.skip("No equipments in core.dim_equipment")

    next_workout_number = get_max_workout_number(user_id) + 1
    today = date.today().isoformat()

    # Login via SPA
    page.goto(f"{frontend_url}/pages/auth/login.html")
    page.wait_for_load_state("networkidle")
    page.fill("#username", username)
    page.fill("#password", password)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    expect(page).to_have_url(f"{frontend_url}/index.html", timeout=10000)

    # Navigate to SPA workout input page
    page.goto(f"{frontend_url}/pages/core/workouts_input.html")
    page.wait_for_load_state("networkidle")

    # Fill the form
    page.wait_for_selector("#exercises_list option", state="attached", timeout=1000)
    page.fill("#exercise_name", exercise["exercise_name"])
    page.fill("#equipment_name", equipment["equipment_name"])
    page.fill("#set_number", "1")
    page.fill("#repetitions", "10")
    page.fill("#load", "50")
    page.fill("#workout_number", str(next_workout_number))
    page.fill("#date", today)
    page.fill("#workout_split", "E2E test split")
    page.fill("#comments", "This is such a bad test, isn't it?")

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

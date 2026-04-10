import os
from datetime import date

import pytest
from playwright.sync_api import Page, expect

from tests.constants import E2E_DASHBOARD_WORKOUT_SPLIT, E2E_TESTER_NAME, E2E_TESTER_PASS


@pytest.mark.order(3)
def test_workout_form_submit_then_delete(page: Page, frontend_url: str, e2e_user_bootstrapped):
    username, password = E2E_TESTER_NAME, E2E_TESTER_PASS

    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL must be set for workout form test")

    today = date.today().isoformat()

    # Login via SPA
    page.goto(f"{frontend_url}/pages/auth/login.html")
    page.wait_for_load_state("networkidle")
    page.fill("#username", username)  # type: ignore[arg-type]
    page.fill("#password", password)  # type: ignore[arg-type]
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    expect(page).to_have_url(f"{frontend_url}/index.html", timeout=10000)

    # Navigate to SPA workout input page
    page.goto(f"{frontend_url}/pages/core/workouts_input.html")
    page.wait_for_load_state("networkidle")

    # Fill the form
    page.wait_for_selector("#exercises_list option", state="attached", timeout=1000)
    page.fill("#exercise_name", "Romanian deadlift")
    page.fill("#equipment_name", "Olympic Barbell")
    page.fill("#set_number", "1")
    page.fill("#repetitions", "10")
    page.fill("#load", "50")
    page.fill("#date", today)
    page.fill("#workout_split", E2E_DASHBOARD_WORKOUT_SPLIT)
    page.fill("#comments", "This is such a bad test, isn't it?")

    # Submit — SPA form submits via fetch(), no page reload
    page.click("#submit-btn")

    # Wait for success message to appear
    msg = page.locator("#message")
    expect(msg).to_contain_text("Workout saved", timeout=10000)

    page.click("#delete-last-btn")
    msg = page.locator("#message")

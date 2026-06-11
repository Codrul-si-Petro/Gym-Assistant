import os

import pytest
from playwright.sync_api import Page, expect

from tests.constants import E2E_DASHBOARD_WORKOUT_SPLIT
from tests.e2e.helpers import goto_core_page


@pytest.mark.order(3)
def test_workout_form_submit_then_delete(page: Page, frontend_url: str, e2e_user_bootstrapped):
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL must be set for workout form test")

    goto_core_page(page, frontend_url, "workouts_input.html")

    page.wait_for_selector("#exercises_list option", state="attached", timeout=15000)
    page.fill("#exercise_name", "Triceps extension")
    page.fill("#equipment_name", "Olympic Barbell")
    page.fill("#set_number", "1")
    page.fill("#set_type", "Working set")
    page.fill("#repetitions", "10")
    page.fill("#load", "50")
    page.fill("#workout_split", E2E_DASHBOARD_WORKOUT_SPLIT)
    page.fill("#comments", "This is such a bad test, isn't it?")

    page.click("#submit-btn")

    msg = page.locator("#message")
    expect(msg).to_contain_text("Workout saved", timeout=10000)

    page.click("#delete-last-btn")
    expect(msg).to_contain_text("Deleted", timeout=10000)

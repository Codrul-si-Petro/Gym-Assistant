import os
import re

import pytest
from playwright.sync_api import Page, expect

from tests.constants import E2E_TODAY_FLOW_SPLIT
from tests.e2e.helpers import (
    browser_today_iso,
    cleanup_e2e_today_flow_data,
    fill_plan_exercise_block,
    goto_core_page,
)

EXERCISE_A = "Triceps extension"
EXERCISE_B = "Biceps curl"

PLAN_SETS_A = [(10, 25), (10, 20)]
PLAN_SETS_B = [(12, 30), (12, 25)]
ALTERED_LAST_REPS = 14
ALTERED_LAST_LOAD = 22


def _submit_logged_set(page: Page) -> None:
    with page.expect_response(
        lambda res: "/api/workouts/" in res.url and res.request.method == "POST" and res.ok,
        timeout=15000,
    ):
        page.click("#submit-btn")


def _expect_log_prefill(page: Page, exercise_name: str, reps: int, load: int) -> None:
    expect(page.locator("#exercise_name")).to_have_value(exercise_name, timeout=10000)
    expect(page.locator("#repetitions")).to_have_value(str(reps), timeout=10000)
    expect(page.locator("#load")).to_have_value(str(load), timeout=10000)


def _fetch_today_actuals(e2e_user_bootstrapped, today_iso: str) -> list[dict]:
    res = e2e_user_bootstrapped.session.get(
        f"{e2e_user_bootstrapped.base}/api/workouts/",
        params={
            "scenario": "actuals",
            "start_date": today_iso,
            "end_date": today_iso,
            "workout_split": E2E_TODAY_FLOW_SPLIT,
            "page_size": 50,
        },
    )
    assert res.status_code == 200, res.text
    payload = res.json()
    rows = payload["results"] if isinstance(payload, dict) else payload
    return sorted(rows, key=lambda row: (row["exercise"], row["set_number"]))


@pytest.mark.order(8)
def test_today_plan_log_flow_with_altered_last_set(
    page: Page,
    frontend_url: str,
    e2e_user_bootstrapped,
):
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL must be set for Today flow E2E test")

    cleanup_e2e_today_flow_data(e2e_user_bootstrapped)

    goto_core_page(page, frontend_url, "workouts_plan.html")
    page.wait_for_selector("#exercises_list option", state="attached", timeout=15000)

    today_iso = browser_today_iso(page)
    page.fill("#plan_label", E2E_TODAY_FLOW_SPLIT)
    page.fill("#plan_workout_split", E2E_TODAY_FLOW_SPLIT)
    page.fill("#plan_start_date", today_iso)
    page.locator('input[name="repeat_type"][value="once"]').check()

    fill_plan_exercise_block(page.locator(".plan-exercise-block").first, EXERCISE_A, PLAN_SETS_A)
    page.locator("#add_exercise_btn").click()
    fill_plan_exercise_block(page.locator(".plan-exercise-block").nth(1), EXERCISE_B, PLAN_SETS_B)

    with page.expect_response(
        lambda res: "/api/plan-series/" in res.url and res.request.method == "POST" and res.ok,
        timeout=15000,
    ):
        page.locator("#submit-btn").click()

    expect(page.locator("#message")).to_contain_text("Plan saved", timeout=10000)

    goto_core_page(page, frontend_url, "today.html")
    expect(page.locator(".today-plan-title")).to_have_text("Today's workout", timeout=10000)
    expect(page.locator(".today-exercise-name").nth(0)).to_have_text(EXERCISE_A)
    expect(page.locator(".today-exercise-name").nth(1)).to_have_text(EXERCISE_B)

    page.locator(".today-log-btn").first.click()
    expect(page).to_have_url(re.compile(r"workouts_input\.html\?"), timeout=10000)
    expect(page.locator("#back-to-today-link")).to_be_visible()

    _expect_log_prefill(page, EXERCISE_A, PLAN_SETS_A[0][0], PLAN_SETS_A[0][1])
    _submit_logged_set(page)
    expect(page.locator("#message")).to_contain_text(f"Next: {EXERCISE_A} — set 2.", timeout=10000)
    _expect_log_prefill(page, EXERCISE_A, PLAN_SETS_A[1][0], PLAN_SETS_A[1][1])

    _submit_logged_set(page)
    expect(page.locator("#message")).to_contain_text(f"Next: {EXERCISE_B} — set 1.", timeout=10000)
    _expect_log_prefill(page, EXERCISE_B, PLAN_SETS_B[0][0], PLAN_SETS_B[0][1])

    _submit_logged_set(page)
    expect(page.locator("#message")).to_contain_text(f"Next: {EXERCISE_B} — set 2.", timeout=10000)
    _expect_log_prefill(page, EXERCISE_B, PLAN_SETS_B[1][0], PLAN_SETS_B[1][1])

    page.fill("#repetitions", str(ALTERED_LAST_REPS))
    page.fill("#load", str(ALTERED_LAST_LOAD))
    _submit_logged_set(page)
    expect(page).to_have_url(re.compile(r"today\.html$"), timeout=15000)

    actuals = _fetch_today_actuals(e2e_user_bootstrapped, today_iso)
    assert len(actuals) == 4
    assert actuals[0]["repetitions"] == PLAN_SETS_A[0][0]
    assert float(actuals[0]["load"]) == PLAN_SETS_A[0][1]
    assert actuals[1]["repetitions"] == PLAN_SETS_A[1][0]
    assert float(actuals[1]["load"]) == PLAN_SETS_A[1][1]
    assert actuals[2]["repetitions"] == PLAN_SETS_B[0][0]
    assert float(actuals[2]["load"]) == PLAN_SETS_B[0][1]
    assert actuals[3]["repetitions"] == ALTERED_LAST_REPS
    assert float(actuals[3]["load"]) == ALTERED_LAST_LOAD

    cleanup_e2e_today_flow_data(e2e_user_bootstrapped, today_iso)

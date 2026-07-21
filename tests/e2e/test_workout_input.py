import os

import pytest
from playwright.sync_api import Page, expect

from tests.constants import (
    E2E_DASHBOARD_WORKOUT_SPLIT,
    E2E_FUTURE_PLAN_DATE,
    E2E_FUTURE_PLAN_EXERCISE_ID,
    E2E_FUTURE_PLAN_LABEL,
)
from tests.e2e.helpers import (
    cleanup_plan_conflicts_on_date,
    delete_plan_series_by_label,
    fill_plan_exercise_block,
    goto_core_page,
)


@pytest.mark.order(3)
def test_workout_form_submit_then_delete(page: Page, frontend_url: str, e2e_user_bootstrapped):
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL must be set for workout form test")

    goto_core_page(page, frontend_url, "workouts_input.html")

    page.wait_for_selector("#exercises_list option", state="attached", timeout=15000)
    page.fill("#exercise_name", "Triceps extension")
    page.fill("#equipment_name", "Olympic Barbell")
    page.fill("#set_type", "Working set")
    page.fill("#repetitions", "10")
    page.fill("#load", "50")
    page.fill("#workout_split", E2E_DASHBOARD_WORKOUT_SPLIT)
    page.fill("#comments", "This is such a bad test, isn't it?")

    page.click("#submit-btn")

    msg = page.locator("#message")
    expect(msg).to_contain_text("Saved:", timeout=10000)

    page.click("#delete-last-btn")
    expect(msg).to_contain_text("Deleted", timeout=10000)


@pytest.mark.order(4)
def test_plan_mode_stamps_future_dates(page: Page, frontend_url: str, e2e_user_bootstrapped):
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL must be set for plan form test")

    cleanup_plan_conflicts_on_date(
        e2e_user_bootstrapped,
        E2E_FUTURE_PLAN_DATE,
        E2E_FUTURE_PLAN_EXERCISE_ID,
    )
    delete_plan_series_by_label(e2e_user_bootstrapped, E2E_FUTURE_PLAN_LABEL)
    delete_plan_series_by_label(e2e_user_bootstrapped, E2E_DASHBOARD_WORKOUT_SPLIT)

    goto_core_page(page, frontend_url, "workouts_plan.html")
    page.wait_for_selector("#exercises_list option", state="attached", timeout=15000)

    page.fill("#plan_label", E2E_FUTURE_PLAN_LABEL)
    page.fill("#plan_start_date", E2E_FUTURE_PLAN_DATE)
    page.locator('input[name="repeat_type"][value="once"]').check()

    fill_plan_exercise_block(
        page.locator(".plan-exercise-block").first,
        "Triceps extension",
        [(12, 35)],
    )

    with page.expect_response(
        lambda res: "/api/plan-series/" in res.url and res.request.method == "POST" and res.ok,
        timeout=15000,
    ):
        page.locator("#submit-btn").click()

    expect(page.locator("#message")).to_contain_text("Plan saved", timeout=10000)
    expect(page.locator(".my-plan-card")).to_contain_text(E2E_FUTURE_PLAN_LABEL, timeout=10000)

    cleanup_plan_conflicts_on_date(
        e2e_user_bootstrapped,
        E2E_FUTURE_PLAN_DATE,
        E2E_FUTURE_PLAN_EXERCISE_ID,
    )
    delete_plan_series_by_label(e2e_user_bootstrapped, E2E_FUTURE_PLAN_LABEL)


@pytest.mark.order(5)
def test_workout_voice_input_fills_form(page: Page, frontend_url: str, e2e_user_bootstrapped):
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL must be set for workout voice input test")

    # stop()/abort() are asynchronous in real browsers — onend fires on a later tick, not
    # synchronously. This mock replicates that delay so the test actually exercises the
    # "tap to stop still applies the transcript" code path (a prior bug cleared the
    # recognition reference before the async onend arrived, silently dropping everything
    # the user said).
    page.add_init_script(
        """
        window.SpeechRecognition = window.webkitSpeechRecognition = class MockSpeechRecognition {
            constructor() {
                this.lang = "en-US";
                this.continuous = false;
                this.interimResults = false;
                this.maxAlternatives = 1;
                this.onstart = null;
                this.onresult = null;
                this.onerror = null;
                this.onend = null;
            }
            start() {
                const self = this;
                window.__lastSpeechRecognition = self;
                setTimeout(() => {
                    if (self.onstart) self.onstart();
                }, 10);
            }
            stop() {
                const self = this;
                setTimeout(() => {
                    if (self.onend) self.onend();
                }, 50);
            }
            abort() {
                const self = this;
                setTimeout(() => {
                    if (self.onend) self.onend();
                }, 50);
            }
        };
        """
    )

    goto_core_page(page, frontend_url, "workouts_input.html")

    page.wait_for_selector("#exercises_list option", state="attached", timeout=15000)
    expect(page.locator("#mic-btn")).to_be_visible()

    page.click("#mic-btn")
    expect(page.locator("#voice-overlay")).to_be_visible()
    expect(page.locator("#voice-status")).to_contain_text("Listening")

    # Simulate an interim result (still mid-utterance) then a final result — mirrors how
    # continuous + interimResults recognition streams multiple onresult events in the browser.
    page.evaluate(
        """
        () => {
            const rec = window.__lastSpeechRecognition;
            const interimResult = [{ transcript: "triceps extension", confidence: 0.8 }];
            interimResult.isFinal = false;
            rec.onresult({ resultIndex: 0, results: [interimResult] });
        }
        """
    )
    expect(page.locator("#voice-overlay-transcript .voice-word-chip")).to_have_count(2)

    page.evaluate(
        """
        () => {
            const rec = window.__lastSpeechRecognition;
            const finalResult = [{
                transcript: "triceps extension olympic barbell no attachment 10 reps 50 kilos",
                confidence: 0.95,
            }];
            finalResult.isFinal = true;
            rec.onresult({ resultIndex: 0, results: [finalResult] });
        }
        """
    )

    # Tap the overlay's stop button — this is the user-facing control that previously
    # dropped the transcript because of the async stop()/onend race.
    page.click("#voice-overlay-stop")

    expect(page.locator("#voice-overlay")).to_be_hidden(timeout=5000)
    expect(page.locator("#exercise_name")).to_have_value("Triceps extension", timeout=5000)
    expect(page.locator("#equipment_name")).to_have_value("Olympic Barbell")
    expect(page.locator("#attachment_name")).to_have_value("")
    expect(page.locator("#repetitions")).to_have_value("10")
    expect(page.locator("#load")).to_have_value("50")
    expect(page.locator("#unit")).to_have_value("KG")
    expect(page.locator("#voice-status")).to_contain_text("Heard:")
    expect(page.locator("#voice-status")).to_contain_text("review and submit")

    # Regression: dictating just reps/load for the next set (no exercise mentioned) must not
    # blank the exercise field — and must not cascade into clearing equipment/attachment via
    # the sticky-gear lookup for an empty exercise name.
    page.click("#mic-btn")
    expect(page.locator("#voice-overlay")).to_be_visible()

    page.evaluate(
        """
        () => {
            const rec = window.__lastSpeechRecognition;
            const finalResult = [{ transcript: "20 reps 30 kilograms", confidence: 0.95 }];
            finalResult.isFinal = true;
            rec.onresult({ resultIndex: 0, results: [finalResult] });
        }
        """
    )
    page.click("#voice-overlay-stop")

    expect(page.locator("#voice-overlay")).to_be_hidden(timeout=5000)
    expect(page.locator("#repetitions")).to_have_value("20", timeout=5000)
    expect(page.locator("#load")).to_have_value("30")
    expect(page.locator("#exercise_name")).to_have_value("Triceps extension")
    expect(page.locator("#equipment_name")).to_have_value("Olympic Barbell")
    expect(page.locator("#attachment_name")).to_have_value("")

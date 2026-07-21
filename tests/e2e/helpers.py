import re
from datetime import date

import pytest
from playwright.sync_api import Page, expect

from tests.constants import (
    E2E_FUTURE_PLAN_EXERCISE_ID,
    E2E_SEED_WORKOUT_DATE,
    E2E_TESTER_NAME,
    E2E_TODAY_FLOW_SPLIT,
)


def clear_auth_state(page: Page, frontend_url: str) -> None:
    """Drop cookies and localStorage JWT so the next test starts logged out."""
    page.context.clear_cookies()
    page.goto(frontend_url)
    page.evaluate("() => localStorage.clear()")


def login(page: Page, frontend_url: str, username: str, password: str) -> None:
    """SPA login via JWT; waits until home loads and the profile menu is visible."""
    page.goto(f"{frontend_url}/pages/auth/login.html")
    page.locator("#username").fill(username)
    page.locator("#password").fill(password)
    with page.expect_response(lambda res: "/api/token/" in res.url and res.ok):
        page.locator("#loginForm button[type='submit']").click()
    page.wait_for_url(f"{frontend_url}/index.html", timeout=15000)
    page.wait_for_function(
        """() => {
            if (!localStorage.getItem('access_token')) return false;
            return document.querySelector('.profile-trigger') !== null;
        }""",
        timeout=15000,
    )
    expect(page.locator(".profile-trigger")).to_be_visible(timeout=5000)


def ensure_authenticated(page: Page) -> None:
    """Wait until JWT is present and the profile menu has rendered."""
    page.wait_for_function(
        """() => {
            if (!localStorage.getItem('access_token')) return false;
            return document.querySelector('.profile-trigger') !== null;
        }""",
        timeout=15000,
    )
    expect(page.locator(".profile-trigger")).to_be_visible(timeout=5000)


def open_home(page: Page, frontend_url: str) -> None:
    """Open the home page; fail fast if session auth bounced to login."""
    page.goto(f"{frontend_url}/index.html")
    page.wait_for_load_state("networkidle")
    expect(page).not_to_have_url(re.compile(r"login\.html$"))
    ensure_authenticated(page)


def goto_core_page(page: Page, frontend_url: str, filename: str) -> None:
    """Open a protected core page and fail fast if require-auth bounced to login."""
    page.goto(f"{frontend_url}/pages/core/{filename}")
    page.wait_for_load_state("networkidle")
    expect(page).not_to_have_url(re.compile(r"login\.html$"))
    ensure_authenticated(page)


def browser_today_iso(page: Page) -> str:
    """Local calendar date in the browser (matches plan/today JS helpers)."""
    return page.evaluate(
        """() => {
            const d = new Date();
            return (
                d.getFullYear() +
                "-" +
                String(d.getMonth() + 1).padStart(2, "0") +
                "-" +
                String(d.getDate()).padStart(2, "0")
            );
        }"""
    )


def delete_plan_series_by_label(bootstrap, label: str) -> None:
    """Delete all plan series with the given label (plan + scheduled rows)."""
    session = bootstrap.session
    base = bootstrap.base
    res = session.get(f"{base}/api/plan-series/")
    if res.status_code != 200:
        return
    for plan in res.json():
        if plan.get("label") == label:
            session.delete(
                f"{base}/api/plan-series/{plan['plan_series_id']}/",
                params={"scope": "all"},
            )


def cleanup_plan_conflicts_on_date(
    bootstrap,
    plan_date: str,
    exercise_id: int = E2E_FUTURE_PLAN_EXERCISE_ID,
) -> None:
    """Remove any plan series (any label) that already books exercise_id on plan_date."""
    from tests.helpers import db_cursor, get_test_user_id

    session = bootstrap.session
    base = bootstrap.base

    res = session.get(
        f"{base}/api/workouts/",
        params={
            "scenario": "plan",
            "start_date": plan_date,
            "end_date": plan_date,
            "exercise_id": exercise_id,
            "page_size": 200,
        },
    )
    if res.status_code == 200:
        payload = res.json()
        rows = payload["results"] if isinstance(payload, dict) else payload
        series_ids = {row["plan_group_id"] for row in rows if row.get("plan_group_id")}
        for series_id in series_ids:
            session.delete(
                f"{base}/api/plan-series/{series_id}/",
                params={"scope": "all"},
            )

    user_id = get_test_user_id(E2E_TESTER_NAME)
    if not user_id:
        return

    with db_cursor() as cur:
        cur.execute(
            """
            DELETE FROM core.fact_workouts
            WHERE user_id = %s AND scenario = 'plan'
              AND date_id = %s AND exercise_id = %s
            """,
            (user_id, plan_date, exercise_id),
        )
        cur.execute(
            """
            DELETE FROM core.plan_series ps
            WHERE ps.user_id = %s
              AND NOT EXISTS (
                SELECT 1 FROM core.fact_workouts w
                WHERE w.plan_group_id = ps.plan_series_id
              )
            """,
            (user_id,),
        )


def cleanup_e2e_today_flow_data(bootstrap, today_iso: str | None = None) -> None:
    """Remove the Today-flow plan series and any logged/planned rows for that split."""
    from tests.helpers import db_cursor, get_test_user_id

    delete_plan_series_by_label(bootstrap, E2E_TODAY_FLOW_SPLIT)

    user_id = get_test_user_id(E2E_TESTER_NAME)
    if not user_id:
        return

    day = today_iso or date.today().isoformat()

    with db_cursor() as cur:
        cur.execute(
            """
            DELETE FROM core.fact_workouts
            WHERE user_id = %s AND workout_split = %s AND date_id = %s
            """,
            (user_id, E2E_TODAY_FLOW_SPLIT, day),
        )


def fill_plan_exercise_block(block, exercise_name: str, sets: list[tuple[int, int]]) -> None:
    """Fill one plan builder block with an exercise name and reps/load per set."""
    block.locator(".exercise-name").fill(exercise_name)
    while block.locator(".plan-set-row").count() < len(sets):
        block.locator(".add-set").click()
    for idx, (reps, load) in enumerate(sets):
        row = block.locator(".plan-set-row").nth(idx)
        row.locator(".set-reps").fill(str(reps))
        row.locator(".set-load").fill(str(load))


def prepare_dashboard_date_range(page: Page) -> None:
    """Ensure the volume tab loads with the default All period (full history through today)."""
    with page.expect_response(
        lambda res: "/api/v1/total-volume" in res.url and res.request.method == "GET",
        timeout=20000,
    ):
        page.locator(".volume-period-chip[data-period='all']").click()


def click_metrics_tab(page: Page, tab: str) -> None:
    """Activate a metrics tab (tabs use role=tab, not button)."""
    page.locator(f".chart-tab[data-tab='{tab}']").click()


def wait_for_volume_table(page: Page) -> None:
    """Wait for the volume tab to finish loading; skip if analytics has no rows."""
    page.wait_for_function(
        """() => {
            const sk = document.getElementById('chart-skeleton-volume');
            if (sk && !sk.classList.contains('hidden')) return false;
            const table = document.getElementById('volume-table-inner');
            const msg = document.getElementById('chart-msg');
            const tableShown = table && table.style.display !== 'none';
            const text = (msg?.textContent || '').trim();
            if (tableShown) return true;
            if (text.includes('No volume data') || text.includes('Failed to load')) return true;
            return false;
        }""",
        timeout=20000,
    )
    chart_msg = (page.locator("#chart-msg").inner_text() or "").strip()
    if "No volume data" in chart_msg:
        pytest.skip("Dashboard has no volume data — E2E seed/dbt refresh may be required")
    if "Failed to load" in chart_msg:
        pytest.fail(f"Dashboard volume request failed: {chart_msg}")
    expect(page.locator("#volume-table-inner")).to_be_visible(timeout=5000)


def wait_for_favourites_list(page: Page) -> None:
    """Switch to favourites tab and wait for data (or skip when empty)."""
    page.locator("#start_date").fill(E2E_SEED_WORKOUT_DATE)
    page.locator("#end_date").fill(E2E_SEED_WORKOUT_DATE)

    def click_favourites_tab() -> None:
        with page.expect_response(
            lambda res: "/api/v1/favourite-exercises" in res.url and res.request.method == "GET" and res.status == 200,
            timeout=20000,
        ):
            click_metrics_tab(page, "favourites")

    click_favourites_tab()
    expect(page.locator("#tab-favourites")).to_have_class(re.compile(r"\bactive\b"))
    expect(page.locator("#chart-skeleton-favourites")).to_have_class(re.compile(r"hidden"), timeout=15000)

    chart_msg = (page.locator("#chart-msg").inner_text() or "").strip()
    if "Failed to load" in chart_msg:
        click_metrics_tab(page, "volume")
        page.wait_for_timeout(300)
        click_favourites_tab()
        expect(page.locator("#chart-skeleton-favourites")).to_have_class(re.compile(r"hidden"), timeout=15000)
        chart_msg = (page.locator("#chart-msg").inner_text() or "").strip()

    if "No data" in chart_msg:
        pytest.skip("No favourite exercise data for seeded user")
    if "Failed to load" in chart_msg:
        pytest.fail(f"Favourite exercises chart failed to load: {chart_msg}")

    expect(page.locator("#tab-favourites .chart-inner")).to_be_visible(timeout=5000)
    expect(page.locator("#fav-exercises-list .stat-row").first).to_be_visible(timeout=5000)

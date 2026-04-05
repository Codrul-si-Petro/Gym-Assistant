import re
from datetime import date

import pytest
from playwright.sync_api import Page, expect


def _login(page: Page, frontend_url: str, username: str, password: str) -> None:
    page.goto(f"{frontend_url}/pages/auth/login.html")
    page.wait_for_load_state("networkidle")
    page.fill("#username", username)
    page.fill("#password", password)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    expect(page).to_have_url(f"{frontend_url}/index.html", timeout=10000)


def _wide_date_range(page: Page) -> None:
    """Widen range so API is more likely to return rows (triggers change handlers)."""
    today = date.today().isoformat()
    page.locator("#start_date").fill("2020-01-01")
    page.locator("#end_date").fill(today)
    page.locator("#end_date").dispatch_event("change")


@pytest.mark.order(5)
def test_dashboard_tabs_switch_and_volume_table_and_drill(
    page: Page,
    test_credentials: tuple[str, str],
    frontend_url: str,
):
    username, password = test_credentials

    _login(page, frontend_url, username, password)

    page.goto(f"{frontend_url}/pages/core/dashboard.html")
    page.wait_for_load_state("networkidle")
    _wide_date_range(page)
    page.wait_for_load_state("networkidle")

    # --- 1) Tabs: default favourites active, then switch to volume and back ---
    fav_panel = page.locator("#tab-favourites")
    vol_panel = page.locator("#tab-volume")
    expect(fav_panel).to_have_class(re.compile(r"\bactive\b"))
    expect(vol_panel).not_to_have_class(re.compile(r"\bactive\b"))

    page.get_by_role("button", name="Total volumes").click()
    page.wait_for_load_state("networkidle")
    expect(vol_panel).to_have_class(re.compile(r"\bactive\b"))
    expect(fav_panel).not_to_have_class(re.compile(r"\bactive\b"))

    page.get_by_role("button", name="Favourite Exercises").click()
    page.wait_for_load_state("networkidle")
    expect(fav_panel).to_have_class(re.compile(r"\bactive\b"))
    expect(vol_panel).not_to_have_class(re.compile(r"\bactive\b"))

    # --- 2) Both views load data: favourites chart canvas + volume table rows ---
    page.get_by_role("button", name="Favourite Exercises").click()
    page.wait_for_load_state("networkidle")
    expect(page.locator("#chart-skeleton-favourites")).to_have_class(re.compile(r"hidden"))
    expect(page.locator("#fav-exercises-canvas")).to_be_visible()

    page.get_by_role("button", name="Total volumes").click()
    page.wait_for_load_state("networkidle")
    expect(page.locator("#chart-skeleton-volume")).to_have_class(re.compile(r"hidden"))

    rows = page.locator("#volume-table-body tr")
    if rows.count() == 0:
        pytest.skip("No volume rows for this user/date range — cannot assert table data")

    expect(page.locator("#volume-table-inner")).to_be_visible()
    expect(rows.first).to_be_visible()

    # --- 3) Drill down: only if a parent row exists (button with drill class) ---
    drill = page.locator(".volume-exercise-drill").first
    if not drill.count():
        pytest.skip("No drillable exercise (is_leaf false) in volume results")

    expect(page.locator("#volume-toolbar")).to_be_hidden()
    drill.click()
    page.wait_for_load_state("networkidle")

    expect(page.locator("#volume-toolbar")).to_be_visible()
    expect(page.locator("#volume-back-btn")).to_be_visible()
    expect(page.locator("#volume-table-body tr").first).to_be_visible()

    page.locator("#volume-back-btn").click()
    page.wait_for_load_state("networkidle")
    expect(page.locator("#volume-toolbar")).to_be_hidden()

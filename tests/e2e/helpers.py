import re

import pytest
from playwright.sync_api import Page, expect

from tests.constants import E2E_SEED_WORKOUT_DATE


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


def prepare_dashboard_date_range(page: Page) -> None:
    """Set a metrics window that includes the fixed E2E seed workout date."""
    page.locator("#start_date").fill(E2E_SEED_WORKOUT_DATE)
    page.locator("#end_date").fill(E2E_SEED_WORKOUT_DATE)
    with page.expect_response(
        lambda res: "/api/v1/total-volume" in res.url and res.request.method == "GET",
        timeout=20000,
    ):
        page.locator("#end_date").dispatch_event("change")


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

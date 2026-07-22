import pytest
from playwright.sync_api import Page, expect

from tests.e2e.helpers import goto_core_page, open_home


@pytest.mark.order(4)
def test_home_summary_only_on_home_page(page: Page, frontend_url: str, e2e_user_bootstrapped):
    open_home(page, frontend_url)

    expect(page.locator("#home-stats")).to_be_visible(timeout=15000)
    expect(page.locator("#home-inactivity")).not_to_be_empty()
    expect(page.locator("#home-week-trend")).to_be_visible(timeout=15000)
    expect(page.locator("#home-month-trend")).to_be_visible(timeout=15000)
    expect(page.locator("#home-year-trend")).to_be_visible(timeout=15000)
    expect(page.locator("#home-week-trend .home-trend-text")).not_to_be_empty()

    expect(page.locator("#workout-count-card")).to_be_visible(timeout=15000)
    expect(page.locator("#workout-count-week")).not_to_be_empty()
    expect(page.locator("#workout-count-month")).not_to_be_empty()
    expect(page.locator("#workout-count-year")).not_to_be_empty()

    goto_core_page(page, frontend_url, "dashboard.html")
    expect(page.locator("#metrics-summary")).to_have_count(0)
    expect(page.locator("#home-stats")).to_have_count(0)
    expect(page.locator("#workout-count-card")).to_have_count(0)
    expect(page.locator("#metrics-workout-count-card")).to_have_count(0)
    expect(page.locator("#tab-volume")).to_be_visible()
    expect(page.locator(".unit-toggle")).to_be_visible()
    expect(page.locator('.chart-tab[data-tab="sessions"]')).to_be_visible()

    page.locator('.chart-tab[data-tab="sessions"]').click()
    expect(page.locator("#tab-sessions")).to_be_visible()
    expect(page.locator("#sessions-workout-count-card")).to_be_visible(timeout=15000)
    expect(page.locator("#sessions-workout-count-card #workout-count-week")).not_to_be_empty()
    expect(page.locator(".sessions-period-chips")).to_be_visible()
    expect(page.locator("#sessions-table-inner, #chart-skeleton-sessions")).to_be_visible()

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.helpers import goto_core_page, open_home


@pytest.mark.order(4)
def test_home_summary_only_on_home_page(page: Page, frontend_url: str, e2e_user_bootstrapped):
    open_home(page, frontend_url)

    expect(page.locator("#home-stats")).to_be_visible(timeout=15000)
    expect(page.locator("#home-inactivity")).not_to_be_empty()
    expect(page.locator(".info-fab")).to_be_visible()
    page.locator(".info-fab").click()
    expect(page.locator(".info-panel--fab")).to_contain_text("Your summary shows")

    goto_core_page(page, frontend_url, "dashboard.html")
    expect(page.locator("#metrics-summary")).to_have_count(0)
    expect(page.locator("#home-stats")).to_have_count(0)
    expect(page.locator("#tab-volume")).to_be_visible()

import re

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.helpers import click_metrics_tab, goto_core_page, prepare_dashboard_date_range, wait_for_volume_table


@pytest.mark.order(6)
def test_dashboard_default_volume_tab_and_all_metric_views(page: Page, frontend_url: str, e2e_user_bootstrapped):
    goto_core_page(page, frontend_url, "dashboard.html")
    prepare_dashboard_date_range(page)

    expect(page.locator("#metrics-summary")).to_have_count(0)

    vol_panel = page.locator("#tab-volume")
    fav_panel = page.locator("#tab-favourites")
    expect(vol_panel).to_have_class(re.compile(r"\bactive\b"))
    expect(fav_panel).not_to_have_class(re.compile(r"\bactive\b"))

    wait_for_volume_table(page)

    rows = page.locator("#volume-table-body tr")
    if rows.count() == 0:
        pytest.skip("No volume rows for this user/date range — cannot assert table data")
    expect(rows.first).to_be_visible()
    expect(page.locator(".volume-period-chip.is-active")).to_have_text("All")

    spark = page.locator(".volume-minichart-placeholder").first
    if spark.count():
        spark.click()
        page.wait_for_load_state("networkidle")
        expect(page.locator("#volume-daily-chart-block")).to_be_visible()
        page.locator("#volume-daily-close").click()
        page.wait_for_load_state("networkidle")

    drill = page.locator(".volume-exercise-drill").first
    if drill.count():
        expect(page.locator("#volume-toolbar")).to_be_hidden()
        drill.click()
        page.wait_for_load_state("networkidle")
        expect(page.locator("#volume-toolbar")).to_be_visible()
        expect(page.locator("#volume-back-btn")).to_be_visible()
        page.locator("#volume-back-btn").click()
        page.wait_for_load_state("networkidle")

    click_metrics_tab(page, "favourites")
    page.wait_for_load_state("networkidle")
    expect(fav_panel).to_have_class(re.compile(r"\bactive\b"))
    expect(page.locator("#chart-skeleton-favourites")).to_have_class(re.compile(r"hidden"), timeout=15000)
    fav_list = page.locator("#fav-exercises-list")
    expect(fav_list).to_be_visible()
    if fav_list.locator(".stat-row").count() == 0:
        pytest.skip("No favourite exercise data for seeded user")
    expect(fav_list.locator(".stat-row").first).to_be_visible()

    click_metrics_tab(page, "splits")
    page.wait_for_load_state("networkidle")
    expect(page.locator("#chart-skeleton-splits")).to_have_class(re.compile(r"hidden"), timeout=15000)
    expect(page.locator("#workout-splits-canvas")).to_be_visible()

    click_metrics_tab(page, "weekdays")
    page.wait_for_load_state("networkidle")
    expect(page.locator("#chart-skeleton-weekdays")).to_have_class(re.compile(r"hidden"), timeout=15000)
    weekdays_list = page.locator("#gym-weekdays-list")
    expect(weekdays_list).to_be_visible()
    if weekdays_list.locator(".stat-row").count() == 0:
        pytest.skip("No weekday data for seeded user")
    expect(weekdays_list.locator(".stat-row").first).to_be_visible()


@pytest.mark.order(7)
def test_dashboard_mobile_viewport(page: Page, frontend_url: str, e2e_user_bootstrapped):
    page.set_viewport_size({"width": 414, "height": 896})
    goto_core_page(page, frontend_url, "dashboard.html")
    prepare_dashboard_date_range(page)

    expect(page.locator("#tab-volume")).to_have_class(re.compile(r"\bactive\b"))
    wait_for_volume_table(page)

    overflow = page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 2")
    assert overflow, "Dashboard page should not overflow horizontally on mobile"

    # Layout/UX on narrow viewport — chart data is covered in test_dashboard_default_volume_tab_and_all_metric_views
    click_metrics_tab(page, "favourites")
    expect(page.locator("#tab-favourites")).to_have_class(re.compile(r"\bactive\b"))
    expect(page.locator("#tab-favourites h1")).to_be_visible()

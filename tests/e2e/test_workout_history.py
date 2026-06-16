import pytest
from playwright.sync_api import Page, expect

from tests.e2e.helpers import goto_core_page


@pytest.mark.order(7)
def test_workout_history_table_filters_edit_and_info(page: Page, frontend_url: str, e2e_user_bootstrapped):
    goto_core_page(page, frontend_url, "workouts_table.html")

    rows = page.locator(".workout-row")
    expect(rows.first).to_be_visible(timeout=15000)
    if rows.count() == 0:
        pytest.skip("E2E user has no workout rows in history")

    page.locator("#filters-toggle").click()

    split_select = page.locator("#filter-split")
    split_options = split_select.locator("option")
    if split_options.count() > 1:
        split_value = split_options.nth(1).get_attribute("value")
        split_label = split_options.nth(1).inner_text()
        split_select.select_option(split_value or "")
        page.locator("#filters-apply").click()
        page.wait_for_load_state("networkidle")
        split_rows = page.locator(".workout-row")
        if split_rows.count() > 0:
            for i in range(min(split_rows.count(), 5)):
                expect(split_rows.nth(i).locator("td").nth(11)).to_contain_text(split_label)
        page.locator("#filters-clear").click()
        page.wait_for_load_state("networkidle")

    exercise_select = page.locator("#filter-exercise")
    exercise_label = page.locator(".workout-row").first.locator("td").nth(2).inner_text().strip()
    exercise_value = None
    options = exercise_select.locator("option")
    for i in range(options.count()):
        if (options.nth(i).inner_text() or "").strip() == exercise_label:
            exercise_value = options.nth(i).get_attribute("value") or ""
            break
    if exercise_value:
        exercise_select.select_option(exercise_value)
        with page.expect_response(lambda res: "/api/workouts/" in res.url and res.ok):
            page.locator("#filters-apply").click()
        filtered_rows = page.locator(".workout-row")
        expect(filtered_rows.first).to_be_visible(timeout=15000)
        expect(page.locator("#workout-tbody")).not_to_contain_text("Not logged in")
        for i in range(min(filtered_rows.count(), 5)):
            expect(filtered_rows.nth(i).locator("td").nth(2)).to_contain_text(exercise_label)

        page.locator("#filters-clear").click()
        page.wait_for_load_state("networkidle")
        expect(page.locator(".workout-row").first).to_be_visible(timeout=15000)

    first_row = page.locator(".workout-row").first
    workout_id = first_row.get_attribute("data-workout-id")
    assert workout_id
    row_selector = f'.workout-row[data-workout-id="{workout_id}"]'
    original_reps = first_row.locator('td[data-col="reps"]').inner_text()
    new_reps = "77" if original_reps != "77" else "78"

    first_row.click()
    expect(page.locator(".edit-sheet")).to_be_visible()
    page.fill("#edit-repetitions", new_reps)
    page.locator(".edit-sheet-save").click()
    page.wait_for_load_state("networkidle")
    expect(page.locator(".edit-sheet")).not_to_be_visible()
    expect(page.locator(row_selector).locator('td[data-col="reps"]')).to_have_text(new_reps)

    page.reload()
    page.wait_for_load_state("networkidle")
    expect(page.locator(row_selector).locator('td[data-col="reps"]')).to_have_text(new_reps, timeout=15000)

    page.locator(row_selector).click()
    page.fill("#edit-repetitions", original_reps)
    page.locator(".edit-sheet-save").click()
    page.wait_for_load_state("networkidle")

    load_more = page.locator("#load-more-btn")
    if not load_more.is_hidden():
        before = page.locator(".workout-row").count()
        load_more.click()
        page.wait_for_load_state("networkidle")
        assert page.locator(".workout-row").count() >= before

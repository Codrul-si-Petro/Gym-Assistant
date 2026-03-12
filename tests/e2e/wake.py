from playwright.sync_api import Page


def test_wake_and_click_home(page: Page):
    """Wake up server and click the home button"""

    page.goto("https://gym-assistant-2smv.onrender.com/", timeout=180000)
    page.wait_for_load_state("networkidle")  # Wait for page to finish loading

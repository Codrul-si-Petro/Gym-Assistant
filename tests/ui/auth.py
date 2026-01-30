import os

from playwright.async_api import Page


def test_login(page: Page):
    TEST_USER_LOGIN = os.getenv("UI_TESTER_USERNAME")
    TEST_USER_PASS = os.getenv("UI_TESTER_PASS")

    page.goto("https://gym-assistant-2smv.onrender.com/")
    page.wait_for_load_state("networkidle")

    page.click(text="Login")

import pytest
from playwright.sync_api import Page, expect

from tests.constants import BACKEND_URL, SHORTLIVED_E2E_TESTER_NAME, SHORTLIVED_E2E_TESTER_PASS


@pytest.mark.order(1)
def test_signup(page: Page, frontend_url: str):
    page.context.clear_cookies()
    page.goto(frontend_url)
    page.wait_for_load_state("networkidle")

    page.locator("#signup-link").click()
    page.wait_for_load_state("networkidle")

    # here I should assert the redirect url is /accounts/signup/
    expect(page).to_have_url(f"{frontend_url}/pages/auth/signup.html")

    page.fill("#username", SHORTLIVED_E2E_TESTER_NAME)
    page.fill("#email", "GicaRekinu@yahoo.com")
    page.fill("#password1", SHORTLIVED_E2E_TESTER_PASS)
    page.fill("#password2", SHORTLIVED_E2E_TESTER_PASS)

    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")

    expect(page).to_have_url(f"{frontend_url}/pages/auth/login.html")


@pytest.mark.order(2)
def test_login(page: Page, test_credentials: tuple[str, str], frontend_url):
    E2E_TESTER_NAME, E2E_TESTER_PASS = test_credentials

    page.goto(f"{frontend_url}/pages/auth/login.html")
    page.wait_for_load_state("networkidle")

    page.fill("#username", E2E_TESTER_NAME)
    page.fill("#password", E2E_TESTER_PASS)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")

    # Should be redirected to home
    expect(page).to_have_url(f"{frontend_url}/index.html")
    # Verify we're logged in
    expect(page.locator("#logout-link")).to_have_text("Log out", timeout=5000)

    page.context.request.post(f"{BACKEND_URL}/api/auth/delete-account/")

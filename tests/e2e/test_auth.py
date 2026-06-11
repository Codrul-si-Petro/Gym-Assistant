import pytest
from playwright.sync_api import Page, expect

from tests.constants import SHORTLIVED_E2E_TESTER_NAME, SHORTLIVED_E2E_TESTER_PASS
from tests.e2e.helpers import clear_auth_state, login


@pytest.mark.no_auth
@pytest.mark.order(1)
def test_signup(page: Page, frontend_url: str):
    clear_auth_state(page, frontend_url)
    page.wait_for_load_state("networkidle")

    # Unauthenticated header shows CTA links (replaces legacy #signup-link)
    page.get_by_role("link", name="Get started").click()
    page.wait_for_load_state("networkidle")

    expect(page).to_have_url(f"{frontend_url}/pages/auth/signup.html")

    page.fill("#username", SHORTLIVED_E2E_TESTER_NAME)
    page.fill("#email", "GicaRekinu@yahoo.com")
    page.fill("#password1", SHORTLIVED_E2E_TESTER_PASS)
    page.fill("#password2", SHORTLIVED_E2E_TESTER_PASS)

    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")

    expect(page).to_have_url(f"{frontend_url}/pages/auth/login.html")


@pytest.mark.no_auth
@pytest.mark.order(2)
def test_login(page: Page, test_credentials: tuple[str, str], frontend_url: str, e2e_user_bootstrapped):
    clear_auth_state(page, frontend_url)
    username, password = test_credentials
    login(page, frontend_url, username, password)

    # Logged-in state: profile avatar menu (replaces legacy #logout-link)
    page.locator(".profile-trigger").click()
    expect(page.locator("#profile-logout-btn")).to_have_text("Log out")

import pytest
from playwright.sync_api import Page, expect
from tests.helpers import delete_test_user




@pytest.mark.order(1)
def test_signup(page: Page, test_credentials: tuple[str, str], frontend_url: str):

    TEST_USER_LOGIN, TEST_USER_PASS = test_credentials
    page.context.clear_cookies()
    page.goto(frontend_url)
    page.wait_for_load_state("networkidle")

    page.locator("#signup-link").click()
    page.wait_for_load_state("networkidle")

    # here I should assert the redirect url is /accounts/signup/
    expect(page).to_have_url(f"{frontend_url}/pages/auth/signup.html")

    page.fill('#username', TEST_USER_LOGIN)
    page.fill('#email', "GicaRekinu@yahoo.com")
    page.fill('#password1', TEST_USER_PASS)
    page.fill('#password2', TEST_USER_PASS)

    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")

    expect(page).to_have_url(f"{frontend_url}/pages/auth/login.html")



@pytest.mark.order(2)
def test_login(page: Page, test_credentials: tuple[str, str], frontend_url, test_user_cleanup):
    TEST_USER_LOGIN, TEST_USER_PASS = test_credentials

    page.goto(f"{frontend_url}/pages/auth/login.html")
    page.wait_for_load_state("networkidle")

    page.fill('#username', TEST_USER_LOGIN)
    page.fill('#password', TEST_USER_PASS)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")

    # Should be redirected to home
    expect(page).to_have_url(f"{frontend_url}/index.html")
    # Verify we're logged in
    expect(page.locator("#logout-link")).to_have_text("Log out", timeout=5000)

    delete_test_user(TEST_USER_LOGIN)

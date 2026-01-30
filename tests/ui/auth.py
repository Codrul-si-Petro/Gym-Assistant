import os

import psycopg2
import pytest
from playwright.sync_api import Page, expect

TEST_USER_LOGIN = os.getenv("UI_TESTER_USERNAME", "")
TEST_USER_PASS = os.getenv("UI_TESTER_PASS", "")
if not TEST_USER_LOGIN or not TEST_USER_PASS:
    raise ValueError("UI_TESTER_USERNAME and UI_TESTER_PASS must be set")

BASE_URL = "https://gym-assistant-2smv.onrender.com"


def verify_email(email: str):
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    conn.cursor().execute("UPDATE public.account_emailaddress SET verified = true WHERE email = %s", (email,))
    conn.commit()
    conn.cursor().close()
    conn.close()


@pytest.mark.order(1)
def test_signup(page: Page):
    page.context.clear_cookies()
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    page.locator("#item5").evaluate("el => el.click()")  # item 5 is the sign up in homepage.html
    page.wait_for_load_state("networkidle")

    # here I should assert the redirect url is /accounts/signup/
    expect(page).to_have_url(f"{BASE_URL}/accounts/signup/")

    page.fill('input[name="username"]', TEST_USER_LOGIN)
    page.fill('input[name="email"]', "GicaRekinu@yahoo.com")
    page.fill('input[name="password1"]', TEST_USER_PASS)
    page.fill('input[name="password2"]', TEST_USER_PASS)

    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")

    verify_email("gicarekinu@yahoo.com")  # it is stored as lowercase in the db


@pytest.mark.order(2)
def test_login(page: Page):
    page.goto(f"{BASE_URL}/accounts/login/")
    page.wait_for_load_state("networkidle")

    page.fill('input[name="login"]', TEST_USER_LOGIN)
    page.fill('input[name="password"]', TEST_USER_PASS)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")

    # Should be redirected to home
    expect(page).to_have_url(f"{BASE_URL}/")
    # Verify we're logged in
    expect(page.locator("#item4")).to_have_text("Logout", timeout=5000)

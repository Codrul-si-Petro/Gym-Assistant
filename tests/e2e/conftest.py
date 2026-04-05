import os

import pytest

from tests.helpers import (
    cleanup_e2e_dashboard_synthetic_rows,
    delete_test_user,
    get_test_user_id,
    seed_e2e_dashboard_synthetic_rows,
)


@pytest.fixture
def seeded_ui_tester_workouts(test_credentials):
    """
    Run after signup/login tests: UI_TESTER exists, then we insert synthetic fact rows.
    """
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL not set")

    username, _ = test_credentials
    if get_test_user_id(username) is None:
        pytest.skip("UI tester user missing — run signup test first (order)")

    cleanup_e2e_dashboard_synthetic_rows(username)
    assert seed_e2e_dashboard_synthetic_rows(username), "Failed to seed dashboard synthetic workouts"
    yield
    # Optional: cleanup_e2e_dashboard_synthetic_rows(username)


@pytest.fixture(scope="session", autouse=True)
def e2e_ui_tester_lifecycle():
    """
    Before e2e: drop stale UI tester + synthetic rows so signup always sees a clean slate.
    After e2e: same cleanup so the next run / CI job does not inherit this user.
    """
    username = os.getenv("UI_TESTER_USERNAME")
    db_url = os.getenv("DATABASE_URL")
    if not username or not db_url:
        yield
        return
    cleanup_e2e_dashboard_synthetic_rows(username)
    delete_test_user(username)
    yield
    cleanup_e2e_dashboard_synthetic_rows(username)
    delete_test_user(username)  # Usually skip row cleanup here if session teardown deletes the user (CASCADE).

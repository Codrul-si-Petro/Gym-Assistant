import os

import pytest

from tests.helpers import (
    cleanup_e2e_dashboard_synthetic_rows,
    create_test_user,
    seed_e2e_dashboard_synthetic_rows,
)


@pytest.fixture(scope="session", autouse=True)
def ui_tester_session(test_credentials):
    """
    Long-lived UI tester: ensure user exists once per session; only remove synthetic
    dashboard rows on teardown (not the user).
    """
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL not set")

    username, password = test_credentials
    user_id = create_test_user(os.environ["BACKEND_URL"], username, password)
    if user_id is None:
        pytest.skip("Could not create or resolve UI tester user")

    cleanup_e2e_dashboard_synthetic_rows(username)
    yield username, password, user_id
    cleanup_e2e_dashboard_synthetic_rows(username)


@pytest.fixture
def seeded_ui_tester_workouts(ui_tester_session):
    """Seed tagged fact_workouts so dashboard APIs return predictable rows."""
    username, _, _ = ui_tester_session
    assert seed_e2e_dashboard_synthetic_rows(username), "Failed to seed dashboard synthetic workouts"
    yield

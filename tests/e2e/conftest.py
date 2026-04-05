import os

import pytest

from tests.helpers import cleanup_e2e_dashboard_synthetic_rows, seed_e2e_dashboard_synthetic_rows


@pytest.fixture(scope="session", autouse=True)
def e2e_dashboard_synthetic_data():
    """
    Seed core.fact_workouts for UI_TESTER_USERNAME so dashboard e2e tests see data.
    Requires DATABASE_URL and a real user row matching UI_TESTER_USERNAME.
    """
    if not os.getenv("DATABASE_URL"):
        yield
        return

    username = os.getenv("UI_TESTER_USERNAME")
    if not username:
        yield
        return

    seed_e2e_dashboard_synthetic_rows(username)
    yield
    cleanup_e2e_dashboard_synthetic_rows(username)

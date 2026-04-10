"""
Pytest configuration for Django tests.
pytest-django will automatically configure Django settings.
Tests use the actual database instead of creating a test database.
This conftest.py makes sure the frontend and the backend servers are ran. (thanks pytest for not making me use Docker for this)
"""

import os
import subprocess
from pathlib import Path

import pytest

from .constants import BACKEND_URL, FRONTEND_URL
from .helpers import wait_server

# not putting this into the constants file in case I need to move it to another directory
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@pytest.hookimpl(tryfirst=True)
@pytest.fixture(scope="session", autouse=True)
def start_servers():
    """
    Start the local frontend http server along with the Django server
    """

    django_process = subprocess.Popen(
        ["python", "manage.py", "runserver", "--noreload"],  # noreload so django doesnt spawn two processes
        cwd=BASE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    frontend_process = subprocess.Popen(
        ["python", "-m", "http.server", "5500"],
        cwd=FRONTEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print("Waiting for local servers...")

    wait_server(BACKEND_URL, timeout=30)
    wait_server(FRONTEND_URL, timeout=30)

    yield

    # clean up
    django_process.terminate()
    frontend_process.terminate()

    django_process.wait()
    frontend_process.wait()


@pytest.fixture
def backend_url():
    return BACKEND_URL


@pytest.fixture
def frontend_url():
    return FRONTEND_URL


@pytest.fixture(scope="session")
def test_credentials():
    username = os.getenv("UI_TESTER_USERNAME")
    password = os.getenv("UI_TESTER_PASS")

    if not username or not password:
        pytest.skip("UI_TESTER_USERNAME and UI_TESTER_PASS must be set")

    return username, password


@pytest.fixture
def homepage(page, frontend_url):
    page.goto(frontend_url)
    page.wait_for_load_state("networkidle")
    return page

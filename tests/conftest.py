"""
Pytest configuration for Django tests.
pytest-django will automatically configure Django settings.
Tests use the actual database instead of creating a test database.
This conftest.py makes sure the frontend and the backend servers are ran. (thanks pytest for not making me use Docker for this)
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import pytest

from .constants import BACKEND_URL, FRONTEND_URL
from .helpers import wait_server

# not putting this into the constants file in case I need to move it to another directory
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

E2E_SERVER_TIMEOUT = int(os.getenv("E2E_SERVER_TIMEOUT", "30"))


def _host_port(url: str, default_port: int) -> str:
    parsed = urlparse(url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or default_port
    return f"{host}:{port}"


def _frontend_port(url: str) -> int:
    return urlparse(url).port or 5500


def _log_process_output(label: str, process: subprocess.Popen) -> None:
    stdout, stderr = process.communicate(timeout=2)
    if stdout and stdout.strip():
        print(f"--- {label} stdout ---\n{stdout}")
    if stderr and stderr.strip():
        print(f"--- {label} stderr ---\n{stderr}")


def _start_or_raise(cmd: list[str], cwd: Path, label: str, env: dict[str, str] | None = None) -> subprocess.Popen:
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    time.sleep(1)
    if process.poll() is not None:
        _log_process_output(label, process)
        raise RuntimeError(f"{label} exited immediately with code {process.returncode}")
    return process


@pytest.hookimpl(tryfirst=True)
@pytest.fixture(scope="session", autouse=True)
def start_servers(request):
    """
    Start the local frontend http server along with the Django server.
    Only runs for E2E tests (Playwright); unit/meta tests skip server boot.
    """
    if not request.session.items:
        yield
        return

    # pytest-playwright adds the browser fixture to E2E tests only.
    if not any("browser" in item.fixturenames for item in request.session.items):
        yield
        return

    django_addr = _host_port(BACKEND_URL, 8000)
    frontend_port = _frontend_port(FRONTEND_URL)

    # E2E always boots with DEBUG so api_throttle uses the relaxed rate. Without this,
    # a local shell that forgot `load django dev` still runs production 15/min limits
    # and flakes late in the suite (workout history edit save gets 429).
    django_env = {**os.environ, "DJANGO_DEBUG": "True"}
    django_process = _start_or_raise(
        [sys.executable, "manage.py", "runserver", "--noreload", django_addr],
        BASE_DIR,
        "Django",
        env=django_env,
    )

    frontend_process = _start_or_raise(
        [sys.executable, "-m", "http.server", str(frontend_port), "--bind", "127.0.0.1"],
        FRONTEND_DIR,
        "Frontend",
    )

    print("Waiting for local servers...")
    try:
        wait_server(BACKEND_URL, timeout=E2E_SERVER_TIMEOUT)
        wait_server(FRONTEND_URL, timeout=E2E_SERVER_TIMEOUT)
    except RuntimeError:
        _log_process_output("Django", django_process)
        _log_process_output("Frontend", frontend_process)
        django_process.terminate()
        frontend_process.terminate()
        django_process.wait(timeout=5)
        frontend_process.wait(timeout=5)
        raise

    yield

    django_process.terminate()
    frontend_process.terminate()
    django_process.wait(timeout=5)
    frontend_process.wait(timeout=5)


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

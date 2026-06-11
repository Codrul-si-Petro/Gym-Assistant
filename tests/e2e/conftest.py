import pytest
from django.contrib.auth import get_user_model

from tests.constants import (
    E2E_TESTER_NAME,
    E2E_TESTER_PASS,
    FRONTEND_URL,
    SHORTLIVED_E2E_TESTER_NAME,
)
from tests.e2e.helpers import login
from tests.helpers import bootstrap_e2e_test_user

User = get_user_model()


@pytest.fixture(scope="session", autouse=True)
def e2e_user_cleanup(django_db_setup, django_db_blocker):
    """
    Deletes short-lived E2E user after full test session.
    For this piece of shit we have to use the db unblocker because Django + Pytest have rules.
    They seem to be good rules but it's still annoying.
    """

    yield

    with django_db_blocker.unblock():
        User.objects.filter(username=SHORTLIVED_E2E_TESTER_NAME).delete()


@pytest.fixture(scope="session")
def e2e_user_bootstrapped():
    return bootstrap_e2e_test_user()


@pytest.fixture(scope="session")
def e2e_storage_state(browser, e2e_user_bootstrapped):
    """
    Log in the long-lived E2E user once; reuse JWT/localStorage for every test context.
    Auth flow tests opt out via @pytest.mark.no_auth.
    """
    context = browser.new_context()
    page = context.new_page()
    login(page, FRONTEND_URL, E2E_TESTER_NAME, E2E_TESTER_PASS)
    state = context.storage_state()
    page.close()
    context.close()
    return state


@pytest.fixture(scope="session")
def _authenticated_context(browser, e2e_storage_state):
    """One shared browser context for all logged-in E2E tests."""
    context = browser.new_context(storage_state=e2e_storage_state)
    yield context
    context.close()


@pytest.fixture
def context(request, browser, e2e_storage_state):
    """
    Auth tests get a fresh context; everything else reuses the session login.
    Overrides pytest-playwright's per-test context to avoid repeated logins.
    """
    if request.node.get_closest_marker("no_auth"):
        ctx = browser.new_context()
        yield ctx
        ctx.close()
    else:
        yield request.getfixturevalue("_authenticated_context")

import pytest
from django.contrib.auth import get_user_model

from tests.constants import (
    SHORTLIVED_E2E_TESTER_NAME,
)
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

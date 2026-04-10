import logging
import os
import time
from contextlib import contextmanager

import psycopg2
import requests
from django.contrib.auth import get_user_model
from rest_framework.test import ImproperlyConfigured

from backend.core.models import Attachments, Equipment, Exercises

from .constants import BACKEND_URL, E2E_TESTER_NAME, E2E_TESTER_PASS


# will try to remember to use this ffs
class CoreDimensions:
    @staticmethod
    def first_exercise() -> tuple[int, str]:
        obj = Exercises.objects.first()
        if obj is None:
            raise ImproperlyConfigured("No exercises found in this model.")
        return obj.exercise_id, obj.exercise_name

    @staticmethod
    def first_equipment() -> tuple[int, str]:
        obj = Equipment.objects.first()
        if obj is None:
            raise ImproperlyConfigured("No equipment found in this model.")
        return obj.equipment_id, obj.equipment_name

    @staticmethod
    def first_attachment() -> tuple[int, str]:
        obj = Attachments.objects.first()
        if obj is None:
            raise ImproperlyConfigured("No attachments found in this model.")
        return obj.attachment_id, obj.attachment_name


@contextmanager
def db_cursor():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    logging.info("We are now connected to the database!")
    try:
        with conn:
            with conn.cursor() as cur:
                yield cur
    finally:
        conn.close()  # close it regardless of what happens


def wait_server(url: str, timeout: int = 30):
    """
    Poll the server for some time to know when to start running tests
    """
    start = time.time()

    print(f"Waiting for server at {url}...")
    while True:
        try:
            r = requests.get(url)
            if r.status_code < 500:
                return
        except requests.exceptions.ConnectionError:
            pass

        if time.time() - start > timeout:
            raise RuntimeError(f"ERROR: The server at {url} timed out in {timeout}. Maybe increase the timeout limit?")

        time.sleep(2)


# user factory relying on Django internals
def create_test_user(
    username: str = "GigelRekinu", password: str = "GigelRekinas29#", email: str = "gigel_rekinu@yahoo.com"
):
    User = get_user_model()
    test_user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
    )
    return test_user


def get_test_user_id(username: str) -> int | None:
    with db_cursor() as cur:
        cur.execute(
            "SELECT id FROM public.authentication_user WHERE username = %s",
            (username,),
        )
        row = cur.fetchone()
        return row[0] if row else None


class E2EUserBootstrap:
    def __init__(self):
        self.session = requests.Session()
        self.base = BACKEND_URL

    def ensure_user(self):
        """
        Try signup. If already exists -> ignore and continue.
        """

        url = f"{self.base}/api/auth/signup/"

        payload = {
            "username": E2E_TESTER_NAME,
            "email": "e2e@test.com",
            "password1": E2E_TESTER_PASS,
            "password2": E2E_TESTER_PASS,
        }

        res = self.session.post(url, json=payload)

        # Accept both success and "already exists"
        if res.status_code in (201, 200):
            print(res.status_code)
            return

        if res.status_code == 400:
            print(res.status_code)
            # assume "user already exists"
            return

        raise RuntimeError(f"Signup failed: {res.status_code} - {res.text}")


def bootstrap_e2e_test_user():
    b = E2EUserBootstrap()
    b.ensure_user()

import logging
import os
import time
from contextlib import contextmanager

import psycopg2
import requests
from django.contrib.auth import get_user_model
from rest_framework.test import ImproperlyConfigured

from backend.core.models import Attachments, Equipment, Exercises

from .constants import BACKEND_URL, E2E_DASHBOARD_WORKOUT_SPLIT, E2E_TESTER_NAME, E2E_TESTER_PASS


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

    def get_bearer_tokens(self):
        url = f"{self.base}/api/token/"

        payload = {
            "username": E2E_TESTER_NAME,
            "password": E2E_TESTER_PASS,
        }

        tokens = self.session.post(url, json=payload).json()
        tokens = {"access": tokens["access"], "refresh": tokens["refresh"]}
        return tokens

    def attach_auth(self, access_token: str):
        self.session.headers.update({"Authorization": f"Bearer {access_token}"})

    def check_workouts_exist(self):
        url = f"{self.base}/api/workouts/"

        res = self.session.get(url)

        if res.status_code != 200:
            raise RuntimeError(f"Failed to fetch workouts: {res.status_code} - {res.text}")

        data = res.json()
        if not data:
            return False

        return True

    def fill_synthetic_workouts(self):
        url = f"{self.base}/api/workouts/"

        base_payload = {
            "equipment": 1,
            "exercise": 1,
            "workout_split": E2E_DASHBOARD_WORKOUT_SPLIT,
            "date": "2026-04-09",
            "repetitions": 10,
            "load": 20,
            "unit": "KG",
            "set_type": "Working set",
            "comments": "e2e seed",
        }

        for set_number in range(1, 4):
            payload = base_payload.copy()
            payload["set_number"] = set_number  # or vary if needed

            res = self.session.post(url, json=payload)

            if res.status_code not in (200, 201):
                raise RuntimeError(f"Workout seed failed: {res.status_code} - {res.text}")

        # another loop... lazy, I know. I'm tired of this
        # refactor later? hopefully not
        for set_number in range(1, 4):
            payload = base_payload.copy()
            payload["set_number"] = set_number  # or vary if needed
            payload["exercise"] = 3  # 2 is already taken by the workout_input e2e test

            res = self.session.post(url, json=payload)

            if res.status_code not in (200, 201):
                raise RuntimeError(f"Workout seed failed: {res.status_code} - {res.text}")


def bootstrap_e2e_test_user():
    b = E2EUserBootstrap()
    b.ensure_user()
    tokens = b.get_bearer_tokens()
    b.attach_auth(tokens["access"])

    data_exists = b.check_workouts_exist()
    if not data_exists:
        b.fill_synthetic_workouts()

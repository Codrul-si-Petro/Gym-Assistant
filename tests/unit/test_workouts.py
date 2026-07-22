"""
Unit tests for the /api/workouts/ endpoints (list, create, retrieve, partial_update,
next-workout-info, delete last) including the Workout History list filters.

These run against the shared dev DB (see tests/conftest.py); every test is wrapped in a
transaction by pytest-django, so created rows roll back automatically.
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from backend.core.models import Attachments, Calendar, Equipment, Exercises
from tests.helpers import create_test_user

BASE_URL = "/api/workouts/"


@pytest.fixture
def dims(db):
    """First leaf rows of each dimension + a calendar date, skipping if unseeded."""
    exercises = list(Exercises.objects.filter(is_leaf=True).order_by("exercise_id")[:2])
    equipment = Equipment.objects.filter(is_leaf=True).order_by("equipment_id").first()
    attachment = Attachments.objects.filter(is_leaf=True).order_by("attachment_id").first()
    calendar = Calendar.objects.filter(date_id__gte="2025-01-01").order_by("date_id").first()
    if len(exercises) < 2 or equipment is None or attachment is None or calendar is None:
        pytest.skip("Dimension tables are not seeded in this database")
    return {
        "exercise": exercises[0].exercise_id,
        "exercise_alt": exercises[1].exercise_id,
        "equipment": equipment.equipment_id,
        "attachment": attachment.attachment_id,
        "date": calendar.date_id.isoformat(),
    }


def _payload(dims, **overrides):
    payload = {
        "exercise": dims["exercise"],
        "equipment": dims["equipment"],
        "attachment": dims["attachment"],
        "workout_number": 1,
        "set_number": 1,
        "repetitions": 10,
        "load": 50,
        "unit": "KG",
        "set_type": "Working set",
        "comments": "pytest row",
        "workout_split": "Pytest Push",
        "date": dims["date"],
    }
    payload.update(overrides)
    return payload


def _create(client, dims, **overrides):
    response = client.post(BASE_URL, _payload(dims, **overrides), format="json")
    assert response.status_code == status.HTTP_201_CREATED, response.data
    return response.data


def test_workouts_list_unauthenticated_returns_401(api_client):
    response = api_client.get(BASE_URL, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_workouts_create_returns_201(authenticated_client, dims):
    data = _create(authenticated_client, dims)
    assert data["workout_id"] is not None
    assert data["repetitions"] == 10
    assert data["workout_split"] == "Pytest Push"


def test_workouts_create_without_split_or_equipment(authenticated_client, dims):
    payload = _payload(dims)
    del payload["workout_split"]
    del payload["equipment"]
    response = authenticated_client.post(BASE_URL, payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED, response.data
    assert response.data["workout_split"] == "None"
    assert response.data["equipment"] == -1


def test_workouts_create_blank_split_defaults_to_none(authenticated_client, dims):
    data = _create(authenticated_client, dims, workout_split="")
    assert data["workout_split"] == "None"


def test_workouts_list_returns_paginated_rows(authenticated_client, dims):
    _create(authenticated_client, dims)
    response = authenticated_client.get(BASE_URL, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["workout_split"] == "Pytest Push"


def test_workouts_retrieve_returns_200(authenticated_client, dims):
    created = _create(authenticated_client, dims)
    response = authenticated_client.get(f"{BASE_URL}{created['workout_id']}/", format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["workout_id"] == created["workout_id"]


def test_workouts_patch_updates_row(authenticated_client, dims):
    created = _create(authenticated_client, dims)
    response = authenticated_client.patch(
        f"{BASE_URL}{created['workout_id']}/",
        {"repetitions": 12, "load": 60, "comments": "fixed typo"},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK, response.data
    assert response.data["repetitions"] == 12
    assert float(response.data["load"]) == 60
    assert response.data["comments"] == "fixed typo"


def test_workouts_put_updates_row(authenticated_client, dims):
    created = _create(authenticated_client, dims)
    payload = _payload(dims, repetitions=15, load=55, comments="full replace")
    response = authenticated_client.put(
        f"{BASE_URL}{created['workout_id']}/",
        payload,
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK, response.data
    assert response.data["repetitions"] == 15
    assert float(response.data["load"]) == 55
    assert response.data["comments"] == "full replace"


def test_workouts_patch_other_users_row_returns_404(authenticated_client, dims, db):
    created = _create(authenticated_client, dims)

    other_client = APIClient()
    other_user = create_test_user("PytestIntruder", "pytest_intruder_pass1", "intruder@example.com")
    other_client.force_authenticate(user=other_user)

    response = other_client.patch(
        f"{BASE_URL}{created['workout_id']}/",
        {"repetitions": 99},
        format="json",
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_workouts_patch_future_date_returns_400(authenticated_client, dims):
    created = _create(authenticated_client, dims)
    response = authenticated_client.patch(
        f"{BASE_URL}{created['workout_id']}/",
        {"date": "2099-12-31"},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_workouts_patch_future_plan_date_allowed(authenticated_client, dims):
    plan_payload = {
        "dates": ["2026-08-10"],
        "exercise": dims["exercise"],
        "equipment": dims["equipment"],
        "attachment": dims["attachment"],
        "repetitions": 5,
        "load": 20,
        "unit": "KG",
        "workout_split": "Pytest Plan",
    }
    batch = authenticated_client.post(f"{BASE_URL}plan-batch/", plan_payload, format="json")
    assert batch.status_code == status.HTTP_201_CREATED, batch.data

    list_resp = authenticated_client.get(BASE_URL, {"scenario": "plan"}, format="json")
    plan_row = next(r for r in list_resp.data["results"] if r.get("workout_split") == "Pytest Plan")
    response = authenticated_client.patch(
        f"{BASE_URL}{plan_row['workout_id']}/",
        {"date": "2026-08-15", "repetitions": 6},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK, response.data
    assert response.data["repetitions"] == 6


def test_workouts_patch_duplicate_set_number_returns_400(authenticated_client, dims):
    _create(authenticated_client, dims, set_number=1)
    second = _create(authenticated_client, dims, set_number=2)

    response = authenticated_client.patch(
        f"{BASE_URL}{second['workout_id']}/",
        {"set_number": 1},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_workouts_list_filters_by_exercise_and_split(authenticated_client, dims):
    _create(authenticated_client, dims, set_number=1)
    _create(authenticated_client, dims, set_number=2)
    _create(authenticated_client, dims, exercise=dims["exercise_alt"], workout_split="Pytest Pull")

    response = authenticated_client.get(
        BASE_URL,
        {"exercise_id": dims["exercise"], "workout_split": "pytest push"},  # iexact on split
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 2
    for row in response.data["results"]:
        assert row["exercise"] == dims["exercise"]
        assert row["workout_split"] == "Pytest Push"

    response = authenticated_client.get(BASE_URL, {"workout_number": 999}, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 0


def test_workouts_list_filters_by_date_range(authenticated_client, dims):
    _create(authenticated_client, dims)

    response = authenticated_client.get(
        BASE_URL,
        {"start_date": dims["date"], "end_date": dims["date"]},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1

    response = authenticated_client.get(
        BASE_URL,
        {"start_date": "1990-01-01", "end_date": "1990-01-02"},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 0


def test_workouts_list_invalid_filters_return_400(authenticated_client, db):
    response = authenticated_client.get(BASE_URL, {"start_date": "not-a-date"}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = authenticated_client.get(
        BASE_URL,
        {"start_date": "2025-12-01", "end_date": "2025-01-01"},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = authenticated_client.get(BASE_URL, {"exercise_id": "abc"}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_next_workout_info_returns_200(authenticated_client, db):
    response = authenticated_client.get(f"{BASE_URL}next-workout-info/", format="json")
    assert response.status_code == status.HTTP_200_OK
    assert set(response.data.keys()) == {
        "max_workout_number",
        "next_workout_number",
        "hour_elapsed",
        "workout_split",
    }
    assert response.data["next_workout_number"] == 1
    assert response.data["workout_split"] is None


def test_workouts_create_auto_computes_workout_and_set_number(authenticated_client, dims):
    """Client-supplied workout_number/set_number are ignored; server assigns the next values."""
    first = _create(authenticated_client, dims, set_number=99, workout_number=99)
    assert first["workout_number"] == 1
    assert first["set_number"] == 1

    second = _create(authenticated_client, dims, set_number=50, workout_number=50)
    assert second["workout_number"] == 1
    assert second["set_number"] == 2


def test_workouts_create_defaults_split_from_session(authenticated_client, dims):
    _create(authenticated_client, dims, workout_split="Session Push")
    data = _create(authenticated_client, dims, exercise=dims["exercise_alt"], workout_split="")
    assert data["workout_split"] == "Session Push"


def test_workouts_create_explicit_split_overrides_session_default(authenticated_client, dims):
    _create(authenticated_client, dims, workout_split="Session Push")
    data = _create(authenticated_client, dims, workout_split="Session Pull")
    assert data["workout_split"] == "Session Pull"


def test_next_set_info_returns_200(authenticated_client, dims):
    _create(authenticated_client, dims, set_number=1)
    response = authenticated_client.get(
        f"{BASE_URL}next-set-info/",
        {"exercise_id": dims["exercise"]},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data == {
        "exercise_id": dims["exercise"],
        "workout_number": 1,
        "next_set_number": 2,
    }


def test_next_set_info_requires_exercise_id(authenticated_client, db):
    response = authenticated_client.get(f"{BASE_URL}next-set-info/", format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_delete_last_workout_returns_200(authenticated_client, dims):
    _create(authenticated_client, dims)
    response = authenticated_client.delete(f"{BASE_URL}last/", format="json")
    assert response.status_code == status.HTTP_200_OK
    assert "Deleted" in response.data["message"]

    # nothing left to delete
    response = authenticated_client.delete(f"{BASE_URL}last/", format="json")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_plan_batch_stamps_multiple_dates(authenticated_client, dims):
    payload = {
        "dates": ["2026-08-01", "2026-08-02"],
        "exercise": dims["exercise"],
        "equipment": dims["equipment"],
        "attachment": dims["attachment"],
        "repetitions": 8,
        "load": 40,
        "unit": "KG",
        "set_type": "Working set",
        "comments": "plan row",
        "workout_split": "Pytest Plan",
    }
    response = authenticated_client.post(f"{BASE_URL}plan-batch/", payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED, response.data
    assert response.data["count"] == 2

    list_resp = authenticated_client.get(BASE_URL, {"scenario": "plan"}, format="json")
    assert list_resp.status_code == status.HTTP_200_OK
    plan_rows = [r for r in list_resp.data["results"] if r.get("comments") == "plan row"]
    assert len(plan_rows) >= 2


def test_workouts_list_defaults_to_actuals(authenticated_client, dims):
    _create(authenticated_client, dims, comments="actual-only")
    plan_payload = {
        "dates": ["2026-08-03"],
        "exercise": dims["exercise"],
        "equipment": dims["equipment"],
        "attachment": dims["attachment"],
        "repetitions": 5,
        "load": 20,
        "unit": "KG",
        "workout_split": "Pytest Plan",
    }
    authenticated_client.post(f"{BASE_URL}plan-batch/", plan_payload, format="json")

    actuals = authenticated_client.get(BASE_URL, format="json")
    assert all(row.get("scenario", "actuals") == "actuals" for row in actuals.data["results"])

    all_rows = authenticated_client.get(BASE_URL, {"scenario": "all"}, format="json")
    scenarios = {row.get("scenario", "actuals") for row in all_rows.data["results"]}
    assert "actuals" in scenarios
    assert "plan" in scenarios

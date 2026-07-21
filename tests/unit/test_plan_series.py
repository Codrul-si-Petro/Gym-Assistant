"""Unit tests for /api/plan-series/ endpoints."""

from rest_framework import status

from backend.core.constants import SCENARIO_PLAN
from backend.core.models import PlanSeries, Workouts

BASE_URL = "/api/plan-series/"


def _plan_payload(dims, **overrides):
    payload = {
        "label": "Pytest Upper",
        "recurrence": {
            "type": "once",
            "start_date": "2026-09-01",
            "end_date": "2026-09-01",
        },
        "exercises": [
            {
                "exercise": dims["exercise"],
                "sets": [
                    {
                        "reps": 8,
                        "load": 60,
                        "unit": "KG",
                        "equipment": dims["equipment"],
                        "attachment": dims["attachment"],
                        "set_type": "Working set",
                    },
                    {
                        "reps": 6,
                        "load": 70,
                        "unit": "KG",
                        "equipment": dims["equipment"],
                        "attachment": None,
                        "set_type": "Working set",
                    },
                ],
            }
        ],
    }
    payload.update(overrides)
    return payload


def test_plan_series_create_once(authenticated_client, dims):
    response = authenticated_client.post(BASE_URL, _plan_payload(dims), format="json")
    assert response.status_code == status.HTTP_201_CREATED, response.data
    assert response.data["occurrence_count"] == 1
    assert response.data["exercise_count"] == 1
    assert response.data["set_count"] == 2
    assert response.data["plan_series_id"] is not None

    rows = Workouts.objects.filter(plan_group_id=response.data["plan_series_id"], scenario=SCENARIO_PLAN)
    assert rows.count() == 2


def test_plan_series_create_weekly(authenticated_client, dims):
    payload = _plan_payload(
        dims,
        recurrence={
            "type": "weekly",
            "start_date": "2026-09-01",
            "end_date": "2026-09-30",
            "weekdays": ["MON", "WED", "FRI"],
        },
    )
    response = authenticated_client.post(BASE_URL, payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED, response.data
    assert response.data["occurrence_count"] >= 3

    rows = Workouts.objects.filter(plan_group_id=response.data["plan_series_id"], scenario=SCENARIO_PLAN)
    assert rows.count() == response.data["occurrence_count"] * 2


def test_plan_series_list_and_retrieve(authenticated_client, dims):
    created = authenticated_client.post(BASE_URL, _plan_payload(dims), format="json")
    series_id = created.data["plan_series_id"]

    listed = authenticated_client.get(BASE_URL, format="json")
    assert listed.status_code == status.HTTP_200_OK
    assert any(item["plan_series_id"] == series_id for item in listed.data)

    detail = authenticated_client.get(f"{BASE_URL}{series_id}/", format="json")
    assert detail.status_code == status.HTTP_200_OK
    assert detail.data["label"] == "Pytest Upper"
    assert len(detail.data["exercises"]) == 1
    assert len(detail.data["exercises"][0]["sets"]) == 2


def test_plan_series_update_replaces_future_rows(authenticated_client, dims):
    created = authenticated_client.post(
        BASE_URL,
        _plan_payload(
            dims,
            recurrence={
                "type": "weekly",
                "start_date": "2026-10-01",
                "end_date": "2026-10-31",
                "weekdays": ["MON"],
            },
        ),
        format="json",
    )
    series_id = created.data["plan_series_id"]
    before_count = Workouts.objects.filter(plan_group_id=series_id, scenario=SCENARIO_PLAN).count()

    updated_payload = _plan_payload(
        dims,
        label="Pytest Upper v2",
        recurrence={
            "type": "weekly",
            "start_date": "2026-10-01",
            "end_date": "2026-10-31",
            "weekdays": ["MON", "FRI"],
        },
    )
    response = authenticated_client.put(f"{BASE_URL}{series_id}/", updated_payload, format="json")
    assert response.status_code == status.HTTP_200_OK, response.data
    assert response.data["label"] == "Pytest Upper v2"

    after_count = Workouts.objects.filter(plan_group_id=series_id, scenario=SCENARIO_PLAN).count()
    assert after_count >= before_count


def test_plan_series_delete_future(authenticated_client, dims):
    created = authenticated_client.post(
        BASE_URL,
        _plan_payload(
            dims,
            recurrence={
                "type": "weekly",
                "start_date": "2026-11-01",
                "end_date": "2026-12-31",
                "weekdays": ["MON", "WED"],
            },
        ),
        format="json",
    )
    series_id = created.data["plan_series_id"]
    response = authenticated_client.delete(f"{BASE_URL}{series_id}/?scope=future", format="json")
    assert response.status_code == status.HTTP_200_OK

    remaining = Workouts.objects.filter(plan_group_id=series_id, scenario=SCENARIO_PLAN).count()
    assert remaining == 0
    assert not PlanSeries.objects.filter(plan_series_id=series_id).exists()


def test_plan_series_rejects_span_over_one_year(authenticated_client, dims):
    payload = _plan_payload(
        dims,
        recurrence={
            "type": "interval",
            "start_date": "2026-01-01",
            "end_date": "2027-02-01",
            "interval_days": 7,
        },
    )
    response = authenticated_client.post(BASE_URL, payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_plan_series_rejects_past_start_date(authenticated_client, dims):
    payload = _plan_payload(dims, recurrence={"type": "once", "start_date": "2020-01-01", "end_date": "2020-01-01"})
    response = authenticated_client.post(BASE_URL, payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_plan_series_rejects_duplicate_exercise_in_same_plan(authenticated_client, dims):
    payload = _plan_payload(dims)
    payload["exercises"].append(
        {
            "exercise": dims["exercise"],
            "sets": [{"reps": 5, "load": 50, "unit": "KG", "set_type": "Working set"}],
        }
    )
    response = authenticated_client.post(BASE_URL, payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_plan_series_rejects_conflicting_exercise_across_plans(authenticated_client, dims):
    first = authenticated_client.post(
        BASE_URL,
        _plan_payload(dims, recurrence={"type": "once", "start_date": "2026-09-05", "end_date": "2026-09-05"}),
        format="json",
    )
    assert first.status_code == status.HTTP_201_CREATED, first.data

    # Same exercise, same date, but a brand-new plan series — should be rejected.
    second = authenticated_client.post(
        BASE_URL,
        _plan_payload(dims, recurrence={"type": "once", "start_date": "2026-09-05", "end_date": "2026-09-05"}),
        format="json",
    )
    assert second.status_code == status.HTTP_400_BAD_REQUEST

    # A different exercise on the same date is fine.
    third_payload = _plan_payload(
        dims,
        recurrence={"type": "once", "start_date": "2026-09-05", "end_date": "2026-09-05"},
    )
    third_payload["exercises"][0]["exercise"] = dims["exercise_alt"]
    third = authenticated_client.post(BASE_URL, third_payload, format="json")
    assert third.status_code == status.HTTP_201_CREATED, third.data


def test_plan_series_update_does_not_conflict_with_itself(authenticated_client, dims):
    created = authenticated_client.post(
        BASE_URL,
        _plan_payload(
            dims,
            recurrence={
                "type": "weekly",
                "start_date": "2026-10-05",
                "end_date": "2026-10-26",
                "weekdays": ["MON"],
            },
        ),
        format="json",
    )
    assert created.status_code == status.HTTP_201_CREATED, created.data
    series_id = created.data["plan_series_id"]

    updated_payload = _plan_payload(
        dims,
        label="Pytest Upper renamed",
        recurrence={
            "type": "weekly",
            "start_date": "2026-10-05",
            "end_date": "2026-10-26",
            "weekdays": ["MON"],
        },
    )
    response = authenticated_client.put(f"{BASE_URL}{series_id}/", updated_payload, format="json")
    assert response.status_code == status.HTTP_200_OK, response.data

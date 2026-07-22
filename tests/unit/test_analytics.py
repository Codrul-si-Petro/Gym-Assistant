from rest_framework import status


def test_rest_days_unauthenticated_returns_401(api_client):
    response = api_client.get("/api/v1/rest-days", format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_favourite_exercises_invalid_date_range_returns_400(authenticated_client):
    response = authenticated_client.get(
        "/api/v1/favourite-exercises",
        {"start_date": "2025-12-01", "end_date": "2025-01-01"},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_favourite_exercise_returns_200(authenticated_client):
    response = authenticated_client.get("/api/v1/favourite-exercises", format="json")
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response.data
    assert isinstance(response.data["results"], list)


def test_total_volume_authenticated_returns_200(authenticated_client):
    response = authenticated_client.get("/api/v1/total-volume", {"period": "ytd"}, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response.data
    assert response.data.get("period") == "ytd"


def test_total_volume_defaults_to_all(authenticated_client):
    response = authenticated_client.get("/api/v1/total-volume", format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("period") == "all"


def test_total_volume_invalid_period_returns_400(authenticated_client):
    response = authenticated_client.get("/api/v1/total-volume", {"period": "bad"}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_rest_days_authenticated_returns_200(authenticated_client):
    response = authenticated_client.get("/api/v1/rest-days", format="json")
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response.data
    assert "count" in response.data


def test_total_volume_daily_requires_exercise_id(authenticated_client):
    response = authenticated_client.get("/api/v1/total-volume-daily", format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_total_volume_daily_returns_200(authenticated_client):
    response = authenticated_client.get("/api/v1/total-volume-daily", {"exercise_id": 1}, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response.data
    assert isinstance(response.data["results"], list)
    if response.data["results"]:
        row = response.data["results"][0]
        assert "actuals_volume" in row
        assert "plan_volume" in row


def test_workout_splits_returns_200(authenticated_client):
    response = authenticated_client.get("/api/v1/workout-splits", format="json")
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response.data
    assert isinstance(response.data["results"], list)


def test_gym_weekdays_returns_200(authenticated_client):
    response = authenticated_client.get("/api/v1/gym-weekdays", format="json")
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response.data
    assert isinstance(response.data["results"], list)


def test_workout_sessions_returns_200(authenticated_client):
    response = authenticated_client.get("/api/v1/workout-sessions", format="json")
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response.data
    assert "total" in response.data
    assert isinstance(response.data["results"], list)
    assert response.data["total"] == len(response.data["results"])


def test_home_summary_returns_200(authenticated_client):
    response = authenticated_client.get("/api/v1/home-summary", format="json")
    assert response.status_code == status.HTTP_200_OK
    assert set(response.data.keys()) == {
        "days_since_last_workout",
        "total_volume_kg",
        "total_volume_lbs",
        "workouts_this_week",
        "workouts_last_week",
        "workouts_this_month",
        "workouts_last_month",
        "workouts_this_year",
        "workouts_last_year",
        "workouts_planned_this_week",
        "workouts_planned_this_month",
        "workouts_planned_this_year",
        "workouts_planned_week_full",
        "workouts_planned_month_full",
        "workouts_planned_year_full",
    }
    for key in (
        "workouts_this_week",
        "workouts_last_week",
        "workouts_this_month",
        "workouts_last_month",
        "workouts_this_year",
        "workouts_last_year",
        "workouts_planned_this_week",
        "workouts_planned_this_month",
        "workouts_planned_this_year",
        "workouts_planned_week_full",
        "workouts_planned_month_full",
        "workouts_planned_year_full",
    ):
        assert isinstance(response.data[key], int)
        assert response.data[key] >= 0


def test_total_volume_with_parent_id_returns_results(authenticated_client):
    response = authenticated_client.get(
        "/api/v1/total-volume",
        {"parent_id": 48, "period": "ytd"},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response.data
    for row in response.data["results"]:
        assert set(row.keys()) == {
            "exercise_id",
            "exercise_name",
            "is_leaf",
            "total_volume",
            "plan_volume",
            "plan_week_full",
            "plan_month_full",
            "plan_year_full",
            "previous_week",
            "previous_week_to_date",
            "previous_month",
            "previous_month_to_date",
            "previous_year",
            "previous_year_to_date",
            "rank",
        }

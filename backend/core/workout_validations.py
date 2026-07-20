"""
Modules to validate business logic for inputting workouts in the workout form.
Used by core.serializers
"""

from datetime import timedelta

from django.db.models import Max
from django.utils import timezone
from rest_framework import serializers

from .models import Workouts
from .workout_constants import SCENARIO_ACTUALS


def _actuals_qs(user):
    return Workouts.objects.filter(user=user, scenario=SCENARIO_ACTUALS)


def get_next_workout(user):
    """Return the user's current max workout number and whether a new session should start."""
    agg = _actuals_qs(user).aggregate(Max("workout_number"))
    max_num = agg["workout_number__max"]

    if max_num is None:
        return {
            "max_workout_number": None,
            "next_workout_number": 1,
            "hour_elapsed": False,
            "workout_split": None,
        }

    last_created = (
        _actuals_qs(user).order_by("-ta_created_at").values_list("ta_created_at", flat=True).first()
    )
    hour_elapsed = False
    if last_created:
        hour_elapsed = (timezone.now() - last_created) > timedelta(hours=6)

    next_num = max_num + 1 if hour_elapsed else max_num

    workout_split = None
    if not hour_elapsed:
        workout_split = (
            _actuals_qs(user)
            .order_by("-ta_created_at")
            .values_list("workout_split", flat=True)
            .first()
        )

    return {
        "max_workout_number": max_num,
        "next_workout_number": next_num,
        "hour_elapsed": hour_elapsed,
        "workout_split": workout_split,
    }


def get_next_set_number(user, exercise_id, workout_number, scenario=SCENARIO_ACTUALS, date_id=None):
    """Return the next set number for (user, exercise, workout_number), capped at 200."""
    filters = {
        "user": user,
        "exercise_id": exercise_id,
        "workout_number": workout_number,
        "scenario": scenario,
    }
    if date_id is not None:
        filters["date_id"] = date_id
    agg = Workouts.objects.filter(**filters).aggregate(Max("set_number"))
    max_set = agg["set_number__max"] or 0
    return min(max_set + 1, 200)


def validate_workout_number(user, value: int):
    """
    Workout number must be max or max+1 (no skipping, no going backwards).
    If more than the configured time has passed since the last input,
    the user must start a new session (workout_number = max + 1).
    """
    info = get_next_workout(user)
    max_workout_number = info["max_workout_number"]

    next_workout_number = max_workout_number + 1

    if value < max_workout_number:
        raise serializers.ValidationError(
            f"Workout number cannot be less than your current max ({max_workout_number})."
        )
    if value > next_workout_number:
        raise serializers.ValidationError(
            f"Can't skip workout numbers. You are currently doing workout {max_workout_number}."
        )
    if info["hour_elapsed"] and value == max_workout_number:
        raise serializers.ValidationError(
            f"More than 6 hours have passed since your last input. "
            f"You must start a new workout session (workout number {next_workout_number})."
        )

    return value

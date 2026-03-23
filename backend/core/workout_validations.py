"""
Modules to validate business logic for inputting workouts in the workout form.
Used by core.serializers
"""

from datetime import timedelta

from django.db.models import Max
from django.utils import timezone
from rest_framework import serializers

from .models import Workouts


def get_next_workout(user):
    """Return the user's current max workout number and whether a new session should start."""
    agg = Workouts.objects.filter(user=user).aggregate(Max("workout_number"))
    max_num = agg["workout_number__max"]

    if max_num is None:
        return {"max_workout_number": None, "next_workout_number": 1, "hour_elapsed": False}

    last_created = (
        Workouts.objects.filter(user=user).order_by("-ta_created_at").values_list("ta_created_at", flat=True).first()
    )
    hour_elapsed = False
    if last_created:
        hour_elapsed = (timezone.now() - last_created) > timedelta(hours=6)

    next_num = max_num + 1 if hour_elapsed else max_num

    return {
        "max_workout_number": max_num,
        "next_workout_number": next_num,
        "hour_elapsed": hour_elapsed,
    }


def validate_workout_number(user, value: int):
    """
    Workout number must be max or max+1 (no skipping, no going backwards).
    If more than the configured time has passed since the last input,
    the user must start a new session (workout_number = max + 1).
    """
    info = get_next_workout(user)
    max_workout_number = info["max_workout_number"]

    if max_workout_number is None:
        if value != 1:
            raise serializers.ValidationError("This is your first workout. Workout number must be 1.")
        return value

    next_workout_number = max_workout_number + 1

    if value < max_workout_number:
        raise serializers.ValidationError(
            f"Workout number cannot be less than your current max ({max_workout_number})."
        )
    if value > next_workout_number:
        raise serializers.ValidationError(
            f"Can't skip workout numbers. Next allowed is {max_workout_number} or {next_workout_number}."
        )

    if info["hour_elapsed"] and value == max_workout_number:
        raise serializers.ValidationError(
            f"More than 6 hours have passed since your last input. "
            f"You must start a new workout session (workout number {next_workout_number})."
        )

    return value

"""Serializers for workout plan series (multi-exercise, recurring plans)."""

import uuid
from datetime import date

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .constants import PLACEHOLDER_DIMENSION_ID, PLACEHOLDER_DIMENSION_NAME, SCENARIO_PLAN
from .models import Attachments, Calendar, Equipment, Exercises, PlanSeries, Workouts
from .recurrence import RecurrenceError, expand_recurrence

MAX_PLAN_ROWS = 5000
MAX_CONFLICTS_SHOWN = 10


class PlanSetSerializer(serializers.Serializer):
    reps = serializers.IntegerField(min_value=1, max_value=1000)
    load = serializers.FloatField(min_value=0, max_value=1500)
    unit = serializers.ChoiceField(choices=["KG", "LBS"], default="KG")
    equipment = serializers.PrimaryKeyRelatedField(queryset=Equipment.objects.all(), required=False, allow_null=True)
    attachment = serializers.PrimaryKeyRelatedField(queryset=Attachments.objects.all(), required=False, allow_null=True)
    set_type = serializers.CharField(min_length=1, max_length=100, default="Working set")


class PlanExerciseSerializer(serializers.Serializer):
    exercise = serializers.PrimaryKeyRelatedField(queryset=Exercises.objects.all())
    sets = PlanSetSerializer(many=True, min_length=1, max_length=200)


class RecurrenceSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["once", "weekly", "interval"])
    start_date = serializers.DateField()
    end_date = serializers.DateField(required=False, allow_null=True)
    weekdays = serializers.ListField(
        child=serializers.ChoiceField(choices=["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]),
        required=False,
        allow_empty=True,
    )
    interval_days = serializers.IntegerField(min_value=1, max_value=365, required=False, allow_null=True)

    def validate(self, attrs):
        recurrence_type = attrs["type"]
        start = attrs["start_date"]

        if recurrence_type == "once":
            attrs["end_date"] = start
            end = start
        else:
            end = attrs.get("end_date")
            if not end:
                raise serializers.ValidationError({"end_date": "End date is required for recurring plans."})
            if end < start:
                raise serializers.ValidationError({"end_date": "End date must be on or after the start date."})
            attrs["end_date"] = end
            if recurrence_type == "weekly" and not attrs.get("weekdays"):
                raise serializers.ValidationError({"weekdays": "Select at least one weekday."})
            if recurrence_type == "interval" and not attrs.get("interval_days"):
                raise serializers.ValidationError({"interval_days": "Interval days is required."})
        try:
            expand_recurrence(
                start,
                end,
                recurrence_type,
                weekdays=attrs.get("weekdays"),
                interval_days=attrs.get("interval_days"),
            )
        except RecurrenceError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        return attrs


class PlanSeriesSerializer(serializers.Serializer):
    plan_series_id = serializers.UUIDField(read_only=True)
    label = serializers.CharField(max_length=50, allow_blank=False)
    recurrence = RecurrenceSerializer()
    exercises = PlanExerciseSerializer(many=True, min_length=1, max_length=50)
    occurrence_count = serializers.IntegerField(read_only=True)
    exercise_count = serializers.IntegerField(read_only=True)
    set_count = serializers.IntegerField(read_only=True)
    next_date = serializers.DateField(read_only=True, allow_null=True)
    ta_created_at = serializers.DateTimeField(read_only=True)
    ta_updated_at = serializers.DateTimeField(read_only=True)

    def validate_label(self, value):
        stripped = value.strip()
        if not stripped:
            raise serializers.ValidationError("Plan name / split cannot be blank.")
        return stripped

    def validate_exercises(self, value):
        seen = {}
        for block in value:
            ex_id = block["exercise"].pk
            if ex_id in seen:
                raise serializers.ValidationError(
                    f"'{block['exercise'].exercise_name}' is listed in two exercise blocks. "
                    "Combine its sets into a single block."
                )
            seen[ex_id] = True
        return value

    def _resolve_attachment(self, attachment):
        if attachment is None:
            return Attachments.objects.get(pk=PLACEHOLDER_DIMENSION_ID)
        return attachment

    def _resolve_equipment(self, equipment):
        if equipment is None:
            return Equipment.objects.get(pk=PLACEHOLDER_DIMENSION_ID)
        return equipment

    def _total_sets(self, exercises_data):
        return sum(len(block["sets"]) for block in exercises_data)

    def _expand_dates(self, recurrence_data):
        return expand_recurrence(
            recurrence_data["start_date"],
            recurrence_data["end_date"],
            recurrence_data["type"],
            weekdays=recurrence_data.get("weekdays"),
            interval_days=recurrence_data.get("interval_days"),
        )

    def _check_conflicts(self, user, dates, exercises_data, exclude_series_id=None):
        """Block scheduling the same exercise on a date another plan already owns."""
        if not dates:
            return
        exercise_ids = [block["exercise"].pk for block in exercises_data]
        qs = Workouts.objects.filter(
            user=user,
            scenario=SCENARIO_PLAN,
            date_id__in=dates,
            exercise_id__in=exercise_ids,
        )
        if exclude_series_id is not None:
            qs = qs.exclude(plan_group_id=exclude_series_id)
        conflicts = list(
            qs.select_related("exercise")
            .values_list("date_id", "exercise__exercise_name")
            .distinct()
            .order_by("date_id")[:MAX_CONFLICTS_SHOWN]
        )
        if conflicts:
            detail = "; ".join(f"{name} on {d.isoformat()}" for d, name in conflicts)
            raise serializers.ValidationError(
                f"Already planned elsewhere: {detail}. Edit the existing plan instead of double-booking it."
            )

    def _create_workout_rows(self, user, series_id, label, dates, exercises_data):
        total_sets = self._total_sets(exercises_data)
        if len(dates) * total_sets > MAX_PLAN_ROWS:
            raise serializers.ValidationError(
                f"Plan would create {len(dates) * total_sets} rows (max {MAX_PLAN_ROWS})."
            )

        split = label.strip() or PLACEHOLDER_DIMENSION_NAME
        for date_val in dates:
            calendar = Calendar.objects.get(date_id=date_val)
            for block in exercises_data:
                exercise = block["exercise"]
                for set_idx, set_data in enumerate(block["sets"], start=1):
                    # Individual creates (not bulk_create): bulk_create's multi-row INSERT
                    # casts values via UNNEST, which Postgres rejects for the custom
                    # `core.workout_scenario` enum column ("expression is of type
                    # character varying"). Row-by-row create() lets psycopg2 adapt the
                    # scalar value correctly.
                    Workouts.objects.create(
                        user=user,
                        date=calendar,
                        exercise=exercise,
                        attachment=self._resolve_attachment(set_data.get("attachment")),
                        equipment=self._resolve_equipment(set_data.get("equipment")),
                        workout_number=1,
                        set_number=set_idx,
                        repetitions=set_data["reps"],
                        load=set_data["load"],
                        unit=set_data["unit"],
                        set_type=set_data.get("set_type") or "Working set",
                        comments="None",
                        workout_split=split,
                        scenario=SCENARIO_PLAN,
                        plan_group_id=series_id,
                    )
        return len(dates), total_sets

    def _weekdays_to_str(self, weekdays):
        if not weekdays:
            return None
        return ",".join(weekdays)

    def _weekdays_from_str(self, value):
        if not value:
            return []
        return value.split(",")

    def _build_exercises_from_rows(self, rows):
        by_exercise = {}
        for row in rows:
            ex_id = row.exercise_id
            if ex_id not in by_exercise:
                by_exercise[ex_id] = {"exercise": ex_id, "sets": []}
            by_exercise[ex_id]["sets"].append(
                {
                    "reps": row.repetitions,
                    "load": float(row.load),
                    "unit": row.unit,
                    "equipment": row.equipment_id if row.equipment_id != PLACEHOLDER_DIMENSION_ID else None,
                    "attachment": row.attachment_id if row.attachment_id != PLACEHOLDER_DIMENSION_ID else None,
                    "set_type": row.set_type,
                }
            )
        return list(by_exercise.values())

    def _template_rows(self, series_id):
        rows = (
            Workouts.objects.filter(plan_group_id=series_id, scenario=SCENARIO_PLAN)
            .select_related("exercise", "equipment", "attachment")
            .order_by("date_id", "exercise_id", "set_number")
        )
        if not rows:
            return []
        earliest = rows.first().date_id
        return [r for r in rows if r.date_id == earliest]

    def create(self, validated_data):
        user = self.context["request"].user
        recurrence = validated_data["recurrence"]
        exercises_data = validated_data["exercises"]

        if recurrence["start_date"] < date.today():
            raise serializers.ValidationError({"recurrence": {"start_date": "Start date cannot be in the past."}})

        dates = self._expand_dates(recurrence)
        label = validated_data["label"].strip() or PLACEHOLDER_DIMENSION_NAME

        self._check_conflicts(user, dates, exercises_data)

        series_id = uuid.uuid4()
        with transaction.atomic():
            series = PlanSeries.objects.create(
                plan_series_id=series_id,
                user=user,
                label=label,
                recurrence_type=recurrence["type"],
                weekdays=self._weekdays_to_str(recurrence.get("weekdays")),
                interval_days=recurrence.get("interval_days"),
                start_date=recurrence["start_date"],
                end_date=recurrence["end_date"],
            )
            occurrence_count, set_count = self._create_workout_rows(user, series_id, label, dates, exercises_data)

        return {
            "plan_series_id": series_id,
            "label": label,
            "recurrence": recurrence,
            "exercises": self._serialize_exercises_for_response(exercises_data),
            "occurrence_count": occurrence_count,
            "exercise_count": len(exercises_data),
            "set_count": set_count,
            "next_date": self._next_date(series_id),
            "ta_created_at": series.ta_created_at,
            "ta_updated_at": series.ta_updated_at,
        }

    def update(self, instance, validated_data):
        user = self.context["request"].user
        recurrence = validated_data["recurrence"]
        exercises_data = validated_data["exercises"]
        dates = self._expand_dates(recurrence)
        label = validated_data["label"].strip() or PLACEHOLDER_DIMENSION_NAME
        today = date.today()
        future_dates = [d for d in dates if d >= today]

        self._check_conflicts(user, future_dates, exercises_data, exclude_series_id=instance.plan_series_id)

        with transaction.atomic():
            instance.label = label
            instance.recurrence_type = recurrence["type"]
            instance.weekdays = self._weekdays_to_str(recurrence.get("weekdays"))
            instance.interval_days = recurrence.get("interval_days")
            instance.start_date = recurrence["start_date"]
            instance.end_date = recurrence["end_date"]
            instance.ta_updated_at = timezone.now()
            instance.save()

            Workouts.objects.filter(
                plan_group_id=instance.plan_series_id,
                scenario=SCENARIO_PLAN,
                date_id__gte=today,
            ).delete()

            if future_dates:
                self._create_workout_rows(user, instance.plan_series_id, label, future_dates, exercises_data)

        return self.to_representation(instance)

    def _serialize_exercises_for_response(self, exercises_data):
        result = []
        for block in exercises_data:
            sets = []
            for s in block["sets"]:
                equipment = s.get("equipment")
                attachment = s.get("attachment")
                sets.append(
                    {
                        "reps": s["reps"],
                        "load": s["load"],
                        "unit": s["unit"],
                        "equipment": equipment.pk if equipment else None,
                        "attachment": attachment.pk if attachment else None,
                        "set_type": s.get("set_type") or "Working set",
                    }
                )
            result.append({"exercise": block["exercise"].pk, "sets": sets})
        return result

    def _next_date(self, series_id):
        row = (
            Workouts.objects.filter(plan_group_id=series_id, scenario=SCENARIO_PLAN, date_id__gte=date.today())
            .order_by("date_id")
            .values_list("date_id", flat=True)
            .first()
        )
        return row

    def to_representation(self, instance):
        template = self._template_rows(instance.plan_series_id)
        exercises = self._build_exercises_from_rows(template)
        occurrence_count = (
            Workouts.objects.filter(plan_group_id=instance.plan_series_id, scenario=SCENARIO_PLAN)
            .values("date_id")
            .distinct()
            .count()
        )
        set_count = self._total_sets_from_template(exercises)
        return {
            "plan_series_id": instance.plan_series_id,
            "label": instance.label,
            "recurrence": {
                "type": instance.recurrence_type,
                "start_date": instance.start_date,
                "end_date": instance.end_date,
                "weekdays": self._weekdays_from_str(instance.weekdays),
                "interval_days": instance.interval_days,
            },
            "exercises": exercises,
            "occurrence_count": occurrence_count,
            "exercise_count": len(exercises),
            "set_count": set_count,
            "next_date": self._next_date(instance.plan_series_id),
            "ta_created_at": instance.ta_created_at,
            "ta_updated_at": instance.ta_updated_at,
        }

    def _total_sets_from_template(self, exercises):
        return sum(len(block["sets"]) for block in exercises)

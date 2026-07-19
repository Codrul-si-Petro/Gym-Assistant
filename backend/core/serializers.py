import datetime

from django.utils import timezone
from rest_framework import serializers

from .dimension_utils import PLACEHOLDER_DIMENSION_ID, PLACEHOLDER_DIMENSION_NAME
from .models import (
    Attachments,
    Calendar,
    Equipment,
    Exercises,
    Muscles,
    Workouts,
)
from .workout_validations import get_next_set_number, get_next_workout, validate_workout_number


class WorkoutSerializer(serializers.ModelSerializer):
    # define what fields will be read only
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    exercise = serializers.PrimaryKeyRelatedField(queryset=Exercises.objects.all())
    attachment = serializers.PrimaryKeyRelatedField(queryset=Attachments.objects.all(), required=False)
    equipment = serializers.PrimaryKeyRelatedField(
        queryset=Equipment.objects.all(),
        required=False,
    )

    workout_number = serializers.IntegerField(min_value=1, default=1)
    set_number = serializers.IntegerField(min_value=1, max_value=200, default=1)
    repetitions = serializers.IntegerField(min_value=1, max_value=1000, default=0)
    load = serializers.FloatField(min_value=0, default=0, max_value=1500)
    unit = serializers.ChoiceField(default="KG", choices=["KG", "LBS"])
    set_type = serializers.CharField(min_length=1, default="None")
    comments = serializers.CharField(min_length=1, required=False, default="None")
    workout_split = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        default=PLACEHOLDER_DIMENSION_NAME,
    )
    date = serializers.DateField(write_only=True)
    # expose the workout date on reads (the `date` field above is write-only)
    date_id = serializers.DateField(read_only=True)

    class Meta:
        model = Workouts
        fields = [
            "workout_id",
            "user",
            "exercise",
            "attachment",
            "equipment",
            "workout_number",
            "set_number",
            "repetitions",
            "load",
            "unit",
            "set_type",
            "comments",
            "workout_split",
            "date",
            "date_id",
            "ta_created_at",
            "ta_updated_at",
        ]
        read_only_fields = [
            "workout_id",
            "date_id",
            "ta_created_at",
            "user",
            "ta_updated_at",
        ]

    def validate_workout_number(self, value):
        """On create, workout_number is auto-computed in create(); skip strict checks."""
        if self.instance is None:
            return value
        if value == self.instance.workout_number:
            return value
        user = self.context["request"].user
        return validate_workout_number(user, value)

    def validate_date(self, value):
        if value > datetime.date.today():
            raise serializers.ValidationError("Workout date cannot be in the future.")
        return value

    def validate_workout_split(self, value):
        if value is None or (isinstance(value, str) and not value.strip()):
            return PLACEHOLDER_DIMENSION_NAME
        return value.strip()

    def _resolve_calendar_entry(self, date_input):
        try:
            return Calendar.objects.get(date_id=date_input)
        except Calendar.DoesNotExist:
            raise serializers.ValidationError({"date": f"Date {date_input} is outside the supported calendar range."})

    def _resolve_equipment(self, validated_data):
        """DRF field defaults pass raw PKs; Django FKs need model instances."""
        equipment = validated_data.get("equipment")
        if isinstance(equipment, Equipment):
            return
        pk = PLACEHOLDER_DIMENSION_ID if equipment is None else equipment
        validated_data["equipment"] = Equipment.objects.get(pk=pk)

    def create(self, validated_data):
        """Auto-compute workout_number, set_number, and session workout_split on create."""
        date_input = validated_data.pop("date", datetime.date.today())
        validated_data["date"] = self._resolve_calendar_entry(date_input)

        user = self.context["request"].user
        validated_data["user"] = user
        self._resolve_equipment(validated_data)

        info = get_next_workout(user)
        validated_data["workout_number"] = info["next_workout_number"]

        if validated_data.get("workout_split") == PLACEHOLDER_DIMENSION_NAME and info.get("workout_split"):
            validated_data["workout_split"] = info["workout_split"]

        validated_data["set_number"] = get_next_set_number(
            user,
            validated_data["exercise"].pk,
            validated_data["workout_number"],
        )

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Partial update of an existing set row (used by Workout History in-place editing).
        Enforces that the edited row doesn't collide with an existing
        (user, exercise, workout_number, set_number) combination.
        """
        date_input = validated_data.pop("date", None)
        if date_input is not None:
            validated_data["date"] = self._resolve_calendar_entry(date_input)

        if "equipment" in validated_data:
            self._resolve_equipment(validated_data)

        exercise = validated_data.get("exercise", instance.exercise)
        workout_number = validated_data.get("workout_number", instance.workout_number)
        set_number = validated_data.get("set_number", instance.set_number)

        duplicate = (
            Workouts.objects.filter(
                user=instance.user,
                exercise=exercise,
                workout_number=workout_number,
                set_number=set_number,
            )
            .exclude(pk=instance.pk)
            .exists()
        )
        if duplicate:
            raise serializers.ValidationError(
                "This set number already exists for this exercise in this workout. Pick a different set number."
            )

        validated_data["ta_updated_at"] = timezone.now()
        return super().update(instance, validated_data)


class ExercisesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercises
        fields = ["exercise_id", "exercise_name", "exercise_movement_type"]
        read_only_fields = ["exercise_id", "ta_created_at"]


class ExerciseMuscleLinkSerializer(serializers.Serializer):
    muscle_id = serializers.IntegerField()
    muscle_name = serializers.CharField()
    muscle_role = serializers.CharField(allow_null=True)


class ExerciseGlossarySerializer(serializers.Serializer):
    exercise_id = serializers.IntegerField()
    exercise_name = serializers.CharField()
    exercise_movement_type = serializers.CharField()
    muscles = ExerciseMuscleLinkSerializer(many=True)
    youtube_url = serializers.CharField(allow_null=True)
    display_title = serializers.CharField(allow_null=True)
    notes = serializers.CharField(allow_null=True)
    youtube_embed_url = serializers.CharField(allow_null=True)


class MusclesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Muscles
        fields = ["muscle_id", "muscle_name"]
        read_only_fields = ["muscle_id", "ta_created_at"]


class EquipmentSerializer(serializers.ModelSerializer):
    image_url = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = Equipment
        fields = ["equipment_id", "equipment_name", "equipment_description", "equipment_category", "image_url"]
        read_only_fields = ["equipment_id", "ta_created_at"]


class AttachmentSerializer(serializers.ModelSerializer):
    image_url = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = Attachments
        fields = ["attachment_id", "attachment_name", "attachment_description", "image_url"]
        read_only_fields = ["attachment_id", "ta_created_at"]

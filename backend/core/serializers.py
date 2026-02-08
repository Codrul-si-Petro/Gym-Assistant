import datetime

from django.db.models import Max
from rest_framework import serializers

from .models import Attachments, Calendar, Equipment, Exercises, Muscles, Workouts


class WorkoutSerializer(serializers.ModelSerializer):
    # define what fields will be read only
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    exercise = serializers.PrimaryKeyRelatedField(read_only=True)
    attachment = serializers.PrimaryKeyRelatedField(read_only=True)
    equipment = serializers.PrimaryKeyRelatedField(read_only=True)

    # define write only input fields to be associated for FK
    exercise_name = serializers.CharField(write_only=True, required=True)
    attachment_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    equipment_name = serializers.CharField(write_only=True, required=False, allow_blank=True)

    # Other required input fields
    workout_number = serializers.IntegerField(min_value=1, default=1)
    set_number = serializers.IntegerField(min_value=1, max_value=200, default=1)
    repetitions = serializers.IntegerField(min_value=1, max_value=1000, default=0)
    load = serializers.FloatField(min_value=0, default=0, max_value=1500)
    unit = serializers.ChoiceField(default="KG", choices=["KG", "LBS"])
    set_type = serializers.CharField(min_length=1, default="None")
    comments = serializers.CharField(min_length=1, required=False, default="None")
    workout_split = serializers.CharField(max_length=50, min_length=1, default="None")
    date = serializers.DateField(write_only=True)

    class Meta:
        model = Workouts
        fields = [
            "workout_id",
            "user",
            "exercise",
            "exercise_name",
            "attachment",
            "attachment_name",
            "equipment",
            "equipment_name",
            "workout_number",
            "set_number",
            "repetitions",
            "load",
            "unit",
            "set_type",
            "comments",
            "workout_split",
            "date",
            "ta_created_at",
            "ta_updated_at",
        ]
        read_only_fields = [
            "workout_id",
            "ta_created_at",
            "user",
            "exercise",
            "attachment",
            "equipment",
            "ta_updated_at",
        ]

    def validate_exercise_name(self, value):
        """Validate that exercise exists in database"""
        if not Exercises.objects.filter(exercise_name=value).exists():
            raise serializers.ValidationError(f"Exercise '{value}' does not exist in the database.")
        return value

    def validate_attachment_name(self, value):
        """Validate that attachment exists in database, or default to N/A if empty"""
        if not value or not value.strip():
            return "None"
        if not Attachments.objects.filter(attachment_name=value).exists():
            raise serializers.ValidationError(f"Attachment '{value}' does not exist in the database.")
        return value

    def validate_equipment_name(self, value):
        """Validate that equipment exists in database, or default to N/A if empty"""
        if not value or not value.strip():
            return "None"
        if not Equipment.objects.filter(equipment_name=value).exists():
            raise serializers.ValidationError(f"Equipment '{value}' does not exist in the database.")
        return value

    def validate_workout_number(self, value):
        """Workout number must not be less than the user's highest workout number."""
        user = self.context["request"].user
        agg = Workouts.objects.filter(user=user).aggregate(Max("workout_number"))
        max_workout_number = agg["workout_number__max"]
        if max_workout_number is not None and value < max_workout_number:
            raise serializers.ValidationError(
                f"Workout number must be at least {max_workout_number} (your highest so far). You entered {value}."
            )
        return value

    def create(self, validated_data):
        exercise_name = validated_data.pop("exercise_name")
        attachment_name = validated_data.pop("attachment_name", "") or "None"
        equipment_name = validated_data.pop("equipment_name", "") or "None"
        date_input = validated_data.pop("date", datetime.date.today())

        exercise = Exercises.objects.get(exercise_name=exercise_name)
        attachment = Attachments.objects.get(attachment_name=attachment_name)
        equipment = Equipment.objects.get(equipment_name=equipment_name)
        calendar_entry = Calendar.objects.get(date_id=date_input)

        validated_data["exercise"] = exercise
        validated_data["attachment"] = attachment
        validated_data["equipment"] = equipment
        validated_data["date"] = calendar_entry

        # Handle empty workout_split - default to "None" if not provided
        if not validated_data.get("workout_split"):
            validated_data["workout_split"] = "None"

        # auto assign user id
        user = self.context["request"].user
        validated_data["user"] = user

        # Max set_number for this (user, exercise, workout_number); next allowed is max + 1
        agg = Workouts.objects.filter(
            user=user,
            exercise=validated_data["exercise"],
            workout_number=validated_data["workout_number"],
        ).aggregate(Max("set_number"))
        max_set = agg["set_number__max"] or 0
        next_allowed = min(max_set + 1, 200)

        # Don't allow skipping sets
        if validated_data["set_number"] > next_allowed:
            raise serializers.ValidationError(
                f"You can't skip sets. Next set number for this exercise in this workout is {next_allowed}."
            )

        # Don't allow duplicate set numbers
        existing = Workouts.objects.filter(
            user=user,
            exercise=validated_data["exercise"],
            workout_number=validated_data["workout_number"],
            set_number=validated_data["set_number"],
        )
        if existing.exists():
            raise serializers.ValidationError(
                f"This set number already exists for this exercise in this workout. Next set number is {next_allowed}."
            )

        return super().create(validated_data)


class ExercisesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercises
        fields = ["exercise_id", "exercise_name", "exercise_movement_type", "ta_created_at"]
        read_only_fields = ["exercise_id", "ta_created_at"]


class MusclesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Muscles
        fields = "__all__"
        read_only_fields = ["muscle_id", "ta_created_at"]


class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = "__all__"
        read_only_fields = ["equipment_id", "ta_created_at"]


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachments
        fields = "__all__"
        read_only_fields = ["attachment_id", "ta_created_at"]

import datetime

from django.db.models import Max
from rest_framework import serializers

from .models import Attachments, Calendar, Equipment, Exercises, Muscles, Workouts
from .workout_validations import validate_workout_number


class WorkoutSerializer(serializers.ModelSerializer):
    # define what fields will be read only
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    exercise = serializers.PrimaryKeyRelatedField(queryset=Exercises.objects.all())
    attachment = serializers.PrimaryKeyRelatedField(queryset=Attachments.objects.all(), required=False)
    equipment = serializers.PrimaryKeyRelatedField(queryset=Equipment.objects.all())

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
            "ta_created_at",
            "ta_updated_at",
        ]
        read_only_fields = [
            "workout_id",
            "ta_created_at",
            "user",
            "ta_updated_at",
        ]

    def validate_workout_number(self, value):
        """
        DRF calls this automatically for field-level validation.
        This should enforce no workout skipping or goiung backwards, must increment
        after a set period of time ( check the workout_validations.py file)
        """
        user = self.context["request"].user
        return validate_workout_number(user, value)

    def create(self, validated_data):
        """
        Dimensions should be resolved by now
        """

        date_input = validated_data.pop("date", datetime.date.today())
        calendar_entry = Calendar.objects.get(date_id=date_input)
        validated_data["date"] = calendar_entry

        if not validated_data.get("workout_split"):
            validated_data["workout_split"] = "None"
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
        fields = ["exercise_id", "exercise_name", "exercise_movement_type"]
        read_only_fields = ["exercise_id", "ta_created_at"]


class MusclesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Muscles
        fields = ["muscle_id", "muscle_name"]
        read_only_fields = ["muscle_id", "ta_created_at"]


class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = ["equipment_id", "equipment_name", "equipment_description"]
        read_only_fields = ["equipment_id", "ta_created_at"]


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachments
        fields = ["attachment_id", "attachment_name", "attachment_description"]
        read_only_fields = ["attachment_id", "ta_created_at"]

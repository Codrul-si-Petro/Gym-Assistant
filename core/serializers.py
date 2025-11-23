from rest_framework import serializers
from .models import (
        Workouts,
        Exercises,
        Muscles,
        Equipment,
        Attachments
        )

class WorkoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workouts
        fields = '__all__'
        read_only_fields = ['workout_id', 'ta_created_at']

class ExercisesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercises
        fields = [
            'exercise_id',
            'exercise_name',
            'exercise_movement_type',
            'ta_created_at'
            ]
        read_only_fields = ['exercise_id', 'ta_created_at']


class MusclesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Muscles
        fields = '__all__'
        read_only_fields = ['muscle_id', 'ta_created_at']


class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = '__all__'
        read_only_fields = ['equipment_id', 'ta_created_at']


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachments
        fields = '__all__'
        read_only_fields = ['equipment_id', 'ta_created_at']

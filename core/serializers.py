from rest_framework import serializers
from .models import (
        Workouts,
        Exercises
        )

class WorkoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workouts
        fields = '__all__'

class ExercisesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercises
        fields = '__all__'

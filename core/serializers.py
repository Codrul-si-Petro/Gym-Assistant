from rest_framework import serializers
from .models import (
        Workouts,
        Exercises,
        Muscles,
        Equipment,
        Attachments
        )

class WorkoutSerializer(serializers.ModelSerializer):
    # define what fields will be read only
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    exercise = serializers.PrimaryKeyRelatedField(read_only=True)
    attachment = serializers.PrimaryKeyRelatedField(read_only=True)
    equipment = serializers.PrimaryKeyRelatedField(read_only=True)

    # define write only input fields to be associated for FK
    exercise_name = serializers.CharField(write_only=True)
    attachment_name = serializers.CharField(write_only=True)
    equipment_name = serializers.CharField(write_only=True)

    class Meta:
        model = Workouts
        fields = '__all__'
        read_only_fields = ['workout_id', 'ta_created_at']

    def create(self, validated_data):
        exercise_name = validated_data.pop('exercise_name')
        attachment_name = validated_data.pop('attachment_name')

        exercise = Exercises.objects.get(name=exercise_name)
        attachment = Attachments.objects.get(name=attachment_name)

        validated_data['exercise'] = exercise
        validated_data['attachment'] = attachment

        # auto assign user id
        validated_data['user'] = self.context['request'].user

        return super().create(validated_data)

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
        read_only_fields = ['attachment_id', 'ta_created_at']

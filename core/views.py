from .models import (
        Workouts,
        Exercises,
        Muscles,
        Equipment,
        Attachments
        )
from .serializers import (
        WorkoutSerializer,
        ExercisesSerializer,
        MusclesSerializer,
        EquipmentSerializer,
        AttachmentSerializer
        )
from rest_framework.parsers import FormParser, JSONParser
from rest_framework import viewsets
from django.shortcuts import render


def homepageView(request):
    return render(request, "homepage.html")


class WorkoutsViewSet(viewsets.ModelViewSet):
    serializer_class = WorkoutSerializer
    parser_classes = [FormParser, JSONParser]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Workouts.objects.all()
        return Workouts.objects.filter(user=user)


class ExercisesViewSet(viewsets.ModelViewSet):
    serializer_class = ExercisesSerializer
    parser_classes = [FormParser, JSONParser]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Exercises.objects.all()
        return Exercises.objects.filter(user=user)


class MusclesViewSet(viewsets.ModelViewSet):
    serializer_class = MusclesSerializer
    parser_classes = [FormParser, JSONParser]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Exercises.objects.all()
        return Exercises.objects.filter(user=user)


class EquipmentViewSet(viewsets.ModelViewSet):
    serializer_class = EquipmentSerializer
    parser_classes = [FormParser, JSONParser]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Exercises.objects.all()
        return Exercises.objects.filter(user=user)


class AttachmentsViewSet(viewsets.ModelViewSet):
    serializer_class = AttachmentSerializer
    parser_classes = [FormParser, JSONParser]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Exercises.objects.all()
        return Exercises.objects.filter(user=user)

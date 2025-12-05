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
from rest_framework.parsers import FormParser
from rest_framework import viewsets, mixins
from django.shortcuts import render
from .api_throttle import DefaultPostThrottle


def homepageView(request):
    return render(request, "homepage.html")


class WorkoutsViewSet(mixins.CreateModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):

    serializer_class = WorkoutSerializer
    parser_classes = [FormParser]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Workouts.objects.all()
        return Workouts.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_throttles(self):
        if self.request.method == 'GET':  # will remove this probably
            self.throttle_classes = [DefaultPostThrottle]
        if self.request.method == 'POST':
            self.throttle_classes = [DefaultPostThrottle]

        return super().get_throttles()


class ExercisesViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ExercisesSerializer
    parser_classes = [FormParser]

    def get_queryset(self):
        return Exercises.objects.all()

    def get_throttles(self):
        if self.request.method == 'GET':
            self.throttle_classes = [DefaultPostThrottle]
        return super().get_throttles()


class MusclesViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = MusclesSerializer
    parser_classes = [FormParser]

    def get_queryset(self):
        return Muscles.objects.all()


class EquipmentViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = EquipmentSerializer
    parser_classes = [FormParser]

    def get_queryset(self):
        return Equipment.objects.all()


class AttachmentsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = AttachmentSerializer
    parser_classes = [FormParser]

    def get_queryset(self):
        return Attachments.objects.all()

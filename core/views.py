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


class ExercisesViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ExercisesSerializer
    parser_classes = [FormParser]

    def get_queryset(self):
        return Exercises.objects.all()


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

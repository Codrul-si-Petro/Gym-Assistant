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
from rest_framework import viewsets, mixins, request
from django.shortcuts import render
from .api_throttle import EndpointThrottle
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

def homepageView(request):
    return render(request, "homepage.html")

class WorkoutsViewSet(mixins.CreateModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):

    serializer_class = WorkoutSerializer
    parser_classes = [FormParser, JSONParser]
    throttle_classes = [EndpointThrottle]

    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Workouts.objects.all()
        return Workouts.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @swagger_auto_schema(
        request_body=WorkoutSerializer,  # <-- use serializer to avoid writing schema each time
        tags=['Core'],
        consumes=['application/x-www-form-urlencoded']  # <-- force Swagger form
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


    @swagger_auto_schema(tags=["Core"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class ExercisesViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ExercisesSerializer
    parser_classes = [FormParser, JSONParser]
    throttle_classes = [EndpointThrottle]

    def get_queryset(self):
        return Exercises.objects.all()

    @swagger_auto_schema(tags=["Core"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class MusclesViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = MusclesSerializer
    parser_classes = [FormParser, JSONParser]
    throttle_classes = [EndpointThrottle]

    def get_queryset(self):
        return Muscles.objects.all()

    @swagger_auto_schema(tags=["Core"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class EquipmentViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = EquipmentSerializer
    parser_classes = [FormParser, JSONParser]
    throttle_classes = [EndpointThrottle]

    def get_queryset(self):
        return Equipment.objects.all()

    @swagger_auto_schema(tags=["Core"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class AttachmentsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = AttachmentSerializer
    parser_classes = [FormParser, JSONParser]
    throttle_classes = [EndpointThrottle]

    def get_queryset(self):
        return Attachments.objects.all()

    @swagger_auto_schema(tags=["Core"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


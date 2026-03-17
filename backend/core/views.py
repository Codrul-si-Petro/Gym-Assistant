from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser
from rest_framework.response import Response

from backend.core.workout_validations import get_next_workout

from .api_throttle import EndpointThrottle
from .models import Attachments, Equipment, Exercises, Muscles, Workouts
from .serializers import (
    AttachmentSerializer,
    EquipmentSerializer,
    ExercisesSerializer,
    MusclesSerializer,
    WorkoutSerializer,
)


class WorkoutsViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = WorkoutSerializer
    parser_classes = [FormParser, JSONParser]
    throttle_classes = [EndpointThrottle]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Workouts.objects.all().order_by("-date_id")
        return Workouts.objects.filter(user=user).order_by("-date_id")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @swagger_auto_schema(
        request_body=WorkoutSerializer,  # <-- use serializer to avoid writing schema each time
        tags=["Core"],
        consumes=["application/x-www-form-urlencoded"],  # <-- force Swagger form
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Core"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=["get"], url_path="next-workout-info")
    def next_workout_info(self, request):
        return Response(get_next_workout(request.user))


class ExercisesViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ExercisesSerializer
    parser_classes = [FormParser, JSONParser]
    throttle_classes = [EndpointThrottle]

    def get_queryset(self):
        return Exercises.objects.all()

    @swagger_auto_schema(tags=["Core"])
    @method_decorator(cache_page(60 * 60 * 12))  # cache for 12 hrs
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class MusclesViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = MusclesSerializer
    parser_classes = [FormParser, JSONParser]
    throttle_classes = [EndpointThrottle]

    def get_queryset(self):
        return Muscles.objects.all()

    @swagger_auto_schema(tags=["Core"])
    @method_decorator(cache_page(60 * 60 * 12))  # cache for 12 hrs
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class EquipmentViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = EquipmentSerializer
    parser_classes = [FormParser, JSONParser]
    throttle_classes = [EndpointThrottle]

    def get_queryset(self):
        return Equipment.objects.all()

    @swagger_auto_schema(tags=["Core"])
    @method_decorator(cache_page(60 * 60 * 12))  # cache for 12 hrs
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class AttachmentsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = AttachmentSerializer
    parser_classes = [FormParser, JSONParser]
    throttle_classes = [EndpointThrottle]

    def get_queryset(self):
        return Attachments.objects.all()

    @swagger_auto_schema(tags=["Core"])
    @method_decorator(cache_page(60 * 60 * 12))  # cache for 12 hrs
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

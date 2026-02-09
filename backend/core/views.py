from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, viewsets
from rest_framework.parsers import FormParser, JSONParser

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
            return Workouts.objects.all()
        return Workouts.objects.filter(user=user)

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
        accept = request.META.get("HTTP_ACCEPT", "")
        if "text/html" in accept:
            queryset = (
                self.get_queryset()
                .select_related("exercise", "attachment", "equipment", "date")
                .order_by("-ta_created_at")
            )
            content = render_to_string(
                "core/workout_table.html",
                {"rows": queryset},
                request=request,
            )
            return HttpResponse(content, content_type="text/html; charset=utf-8")
        return super().list(request, *args, **kwargs)


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

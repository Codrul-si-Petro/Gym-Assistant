from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser
from rest_framework.response import Response

from backend.core.workout_validations import get_next_workout

from .analytics.cache_utils import invalidate_user_analytics
from .api_throttle import EndpointThrottle
from .models import Attachments, Equipment, Exercise_Muscle_Bridge, ExerciseMedia, Exercises, Muscles, Workouts
from .pagination import WorkoutPagination
from .serializers import (
    AttachmentSerializer,
    EquipmentSerializer,
    ExerciseGlossarySerializer,
    ExercisesSerializer,
    MusclesSerializer,
    WorkoutSerializer,
)


def _youtube_embed_url(url: str | None) -> str | None:
    if not url:
        return None
    if "youtu.be/" in url:
        video_id = url.rsplit("/", 1)[-1].split("?")[0]
        return f"https://www.youtube.com/embed/{video_id}"
    if "v=" in url:
        video_id = url.split("v=")[1].split("&")[0]
        return f"https://www.youtube.com/embed/{video_id}"
    if "/embed/" in url:
        return url
    return None


def _build_glossary_entry(exercise: Exercises) -> dict:
    bridges = Exercise_Muscle_Bridge.objects.filter(exercise=exercise).select_related("muscle")
    muscles = [
        {
            "muscle_id": bridge.muscle.muscle_id,
            "muscle_name": bridge.muscle.muscle_name,
            "muscle_role": bridge.muscle_role,
        }
        for bridge in bridges
    ]
    media = ExerciseMedia.objects.filter(exercise=exercise).first()
    youtube_url = media.youtube_url if media else None
    return {
        "exercise_id": exercise.exercise_id,
        "exercise_name": exercise.exercise_name,
        "exercise_movement_type": exercise.exercise_movement_type,
        "muscles": muscles,
        "youtube_url": youtube_url,
        "display_title": media.display_title if media else None,
        "notes": media.notes if media else None,
        "youtube_embed_url": _youtube_embed_url(youtube_url),
    }


class WorkoutsViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = WorkoutSerializer
    parser_classes = [FormParser, JSONParser]
    throttle_classes = [EndpointThrottle]
    pagination_class = WorkoutPagination

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Workouts.objects.all().order_by("-date_id")
        return Workouts.objects.filter(user=user).order_by("-date_id")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        invalidate_user_analytics(self.request.user.id)

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

    @swagger_auto_schema(
        tags=["Core"],
        operation_description="Delete the most recently created workout row for the current user (by timestamp).",
        responses={204: "No content", 404: "No workouts to delete"},
    )
    @action(detail=False, methods=["delete"], url_path="last")
    def delete_last(self, request):
        qs = Workouts.objects.filter(user=request.user).order_by("-ta_created_at", "-workout_id")
        row = qs.first()
        if row is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        exercise_name = row.exercise.exercise_name
        date_str = row.date_id.isoformat() if row.date_id else ""
        message = (
            f"Deleted: {exercise_name}, {date_str}, "
            f"set {row.set_number}, {row.load} {row.unit} × {row.repetitions} reps"
        )
        row.delete()
        invalidate_user_analytics(request.user.id)

        return Response(
            {
                "message": message,
            },
            status=status.HTTP_200_OK,
        )


class ExercisesViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ExercisesSerializer
    parser_classes = [FormParser, JSONParser]
    throttle_classes = [EndpointThrottle]

    def get_queryset(self):
        return Exercises.objects.filter(is_leaf=True)

    @swagger_auto_schema(tags=["Core"])
    @method_decorator(cache_page(60 * 60 * 12))  # cache for 12 hrs
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Core"], responses={200: ExerciseGlossarySerializer(many=True)})
    @action(detail=False, methods=["get"], url_path="glossary")
    @method_decorator(cache_page(60 * 60 * 12))
    def glossary(self, request):
        exercises = self.get_queryset().order_by("exercise_name")
        payload = [_build_glossary_entry(exercise) for exercise in exercises]
        serializer = ExerciseGlossarySerializer(payload, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(tags=["Core"], responses={200: ExerciseGlossarySerializer()})
    @action(detail=True, methods=["get"], url_path="glossary")
    @method_decorator(cache_page(60 * 60 * 12))
    def glossary_detail(self, request, pk=None):
        exercise = self.get_queryset().filter(pk=pk).first()
        if exercise is None:
            return Response({"detail": "Exercise not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ExerciseGlossarySerializer(_build_glossary_entry(exercise))
        return Response(serializer.data)


class MusclesViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = MusclesSerializer
    parser_classes = [FormParser, JSONParser]
    throttle_classes = [EndpointThrottle]

    def get_queryset(self):
        return Muscles.objects.filter(is_leaf=True)

    @swagger_auto_schema(tags=["Core"])
    @method_decorator(cache_page(60 * 60 * 12))  # cache for 12 hrs
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class EquipmentViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = EquipmentSerializer
    parser_classes = [FormParser, JSONParser]
    throttle_classes = [EndpointThrottle]

    def get_queryset(self):
        return Equipment.objects.filter(is_leaf=True)

    @swagger_auto_schema(tags=["Core"])
    @method_decorator(cache_page(60 * 60 * 12))  # cache for 12 hrs
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class AttachmentsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = AttachmentSerializer
    parser_classes = [FormParser, JSONParser]
    throttle_classes = [EndpointThrottle]

    def get_queryset(self):
        return Attachments.objects.filter(is_leaf=True)

    @swagger_auto_schema(tags=["Core"])
    @method_decorator(cache_page(60 * 60 * 12))  # cache for 12 hrs
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

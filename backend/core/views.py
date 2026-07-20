from django.db.models import OuterRef, Subquery
from django.utils.dateparse import parse_date
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser
from rest_framework.response import Response

from backend.core.workout_validations import get_next_set_number, get_next_workout

from .analytics.cache_utils import invalidate_user_analytics
from .api_throttle import EndpointThrottle
from .constants import SCENARIO_ACTUALS, SCENARIO_PLAN
from .dimension_utils import exclude_placeholder_dimensions
from .glossary.crud.crud import get_exercise_glossary, get_exercise_glossary_list
from .models import AttachmentMedia, Attachments, Equipment, EquipmentMedia, Exercises, Muscles, Workouts
from .pagination import WorkoutPagination
from .serializers import (
    AttachmentSerializer,
    EquipmentSerializer,
    ExerciseGlossarySerializer,
    ExercisesSerializer,
    MusclesSerializer,
    PlanBatchSerializer,
    WorkoutSerializer,
)

WORKOUT_LIST_FILTER_PARAMS = [
    openapi.Parameter("exercise_id", openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
    openapi.Parameter("equipment_id", openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
    openapi.Parameter("workout_number", openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
    openapi.Parameter("workout_split", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("set_type", openapi.IN_QUERY, type=openapi.TYPE_STRING),
    openapi.Parameter("start_date", openapi.IN_QUERY, type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
    openapi.Parameter("end_date", openapi.IN_QUERY, type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
    openapi.Parameter(
        "scenario",
        openapi.IN_QUERY,
        type=openapi.TYPE_STRING,
        enum=[SCENARIO_ACTUALS, SCENARIO_PLAN, "all"],
        description="Filter by scenario; defaults to actuals.",
    ),
]


class WorkoutsViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = WorkoutSerializer
    parser_classes = [FormParser, JSONParser]
    throttle_classes = [EndpointThrottle]
    pagination_class = WorkoutPagination

    def get_queryset(self):
        user = self.request.user
        qs = Workouts.objects.all() if user.is_staff else Workouts.objects.filter(user=user)
        if self.action == "list":
            qs = self._apply_list_filters(qs)
        return qs.order_by("-date_id")

    def _apply_list_filters(self, qs):
        """Server-side column filters for the Workout History table."""
        params = self.request.query_params

        for param, field in (
            ("exercise_id", "exercise_id"),
            ("equipment_id", "equipment_id"),
            ("workout_number", "workout_number"),
        ):
            raw = params.get(param)
            if raw is not None and str(raw).strip() != "":
                try:
                    qs = qs.filter(**{field: int(raw)})
                except ValueError:
                    raise ValidationError({param: "Must be an integer."})

        for param, field in (
            ("workout_split", "workout_split__iexact"),
            ("set_type", "set_type__iexact"),
        ):
            raw = params.get(param)
            if raw is not None and raw.strip() != "":
                qs = qs.filter(**{field: raw.strip()})

        start_raw = params.get("start_date")
        end_raw = params.get("end_date")
        start_date = parse_date(start_raw) if start_raw else None
        end_date = parse_date(end_raw) if end_raw else None
        if start_raw and start_date is None:
            raise ValidationError({"start_date": "Must be an ISO date (YYYY-MM-DD)."})
        if end_raw and end_date is None:
            raise ValidationError({"end_date": "Must be an ISO date (YYYY-MM-DD)."})
        if start_date and end_date and start_date > end_date:
            raise ValidationError({"detail": "Make sure the start date is before the end date."})
        if start_date:
            qs = qs.filter(date_id__gte=start_date)
        if end_date:
            qs = qs.filter(date_id__lte=end_date)

        scenario_raw = params.get("scenario")
        if scenario_raw is None or str(scenario_raw).strip() == "":
            qs = qs.filter(scenario=SCENARIO_ACTUALS)
        elif str(scenario_raw).strip().lower() != "all":
            scenario_val = str(scenario_raw).strip().lower()
            if scenario_val not in (SCENARIO_ACTUALS, SCENARIO_PLAN):
                raise ValidationError({"scenario": f"Must be one of: {SCENARIO_ACTUALS}, {SCENARIO_PLAN}, all."})
            qs = qs.filter(scenario=scenario_val)

        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        invalidate_user_analytics(self.request.user.id)

    def perform_update(self, serializer):
        serializer.save()
        invalidate_user_analytics(self.request.user.id)

    @swagger_auto_schema(
        request_body=WorkoutSerializer,  # <-- use serializer to avoid writing schema each time
        tags=["workout-logging"],
        consumes=["application/x-www-form-urlencoded"],  # <-- force Swagger form
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Core"], manual_parameters=WORKOUT_LIST_FILTER_PARAMS)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Core"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=["workout-logging"],
        request_body=WorkoutSerializer,
        consumes=["application/x-www-form-urlencoded"],  # <-- force Swagger form
        operation_description="Partially update one workout set row owned by the current user.",
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=["Core"],
        request_body=WorkoutSerializer,
        consumes=["application/x-www-form-urlencoded"],  # <-- force Swagger form
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=["workout-logging"],
        consumes=["application/x-www-form-urlencoded"],  # <-- force Swagger form
    )
    @action(detail=False, methods=["get"], url_path="next-workout-info")
    def next_workout_info(self, request):
        return Response(get_next_workout(request.user))

    @swagger_auto_schema(
        tags=["workout-logging"],
        manual_parameters=[
            openapi.Parameter("exercise_id", openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
        ],
    )
    @action(detail=False, methods=["get"], url_path="next-set-info")
    def next_set_info(self, request):
        raw = request.query_params.get("exercise_id")
        if raw is None or str(raw).strip() == "":
            raise ValidationError({"exercise_id": "This query parameter is required."})
        try:
            exercise_id = int(raw)
        except ValueError:
            raise ValidationError({"exercise_id": "Must be an integer."})
        if not Exercises.objects.filter(pk=exercise_id).exists():
            raise ValidationError({"exercise_id": "Exercise not found."})

        info = get_next_workout(request.user)
        workout_number = info["next_workout_number"]
        next_set_number = get_next_set_number(request.user, exercise_id, workout_number)
        return Response(
            {
                "exercise_id": exercise_id,
                "workout_number": workout_number,
                "next_set_number": next_set_number,
            }
        )

    @swagger_auto_schema(
        tags=["Core"],
        operation_description="Delete the most recently created workout row for the current user (by timestamp).",
        responses={204: "No content", 404: "No workouts to delete"},
    )
    @action(detail=False, methods=["delete"], url_path="last")
    def delete_last(self, request):
        qs = Workouts.objects.filter(user=request.user, scenario=SCENARIO_ACTUALS).order_by(
            "-ta_created_at", "-workout_id"
        )
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

    @swagger_auto_schema(
        tags=["workout-logging"],
        request_body=PlanBatchSerializer,
        operation_description="Stamp one planned set onto multiple calendar dates.",
        responses={201: "Created"},
    )
    @action(detail=False, methods=["post"], url_path="plan-batch")
    def plan_batch(self, request):
        serializer = PlanBatchSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        rows = serializer.save()
        invalidate_user_analytics(request.user.id)
        return Response({"count": len(rows)}, status=status.HTTP_201_CREATED)


class ExercisesViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ExercisesSerializer
    parser_classes = [FormParser, JSONParser]
    throttle_classes = [EndpointThrottle]

    def get_queryset(self):
        return exclude_placeholder_dimensions(Exercises.objects.filter(is_leaf=True))

    @swagger_auto_schema(tags=["Core"])
    @method_decorator(cache_page(60 * 60 * 12))  # cache for 12 hrs
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Core"], responses={200: ExerciseGlossarySerializer(many=True)})
    @action(detail=False, methods=["get"], url_path="glossary")
    @method_decorator(cache_page(60 * 60 * 12))
    def glossary(self, request):
        payload = get_exercise_glossary_list()
        serializer = ExerciseGlossarySerializer(payload, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(tags=["Core"], responses={200: ExerciseGlossarySerializer()})
    @action(detail=True, methods=["get"], url_path="glossary")
    @method_decorator(cache_page(60 * 60 * 12))
    def glossary_detail(self, request, pk=None):
        entry = get_exercise_glossary(int(pk))
        if entry is None:
            return Response({"detail": "Exercise not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ExerciseGlossarySerializer(entry)
        return Response(serializer.data)


class MusclesViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = MusclesSerializer
    parser_classes = [FormParser, JSONParser]
    throttle_classes = [EndpointThrottle]

    def get_queryset(self):
        return exclude_placeholder_dimensions(Muscles.objects.filter(is_leaf=True))

    @swagger_auto_schema(tags=["Core"])
    @method_decorator(cache_page(60 * 60 * 12))  # cache for 12 hrs
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class EquipmentViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = EquipmentSerializer
    parser_classes = [FormParser, JSONParser]
    throttle_classes = [EndpointThrottle]

    def get_queryset(self):
        image_url = EquipmentMedia.objects.filter(equipment_id=OuterRef("equipment_id")).values("image_url")[:1]
        return exclude_placeholder_dimensions(
            Equipment.objects.filter(is_leaf=True).annotate(image_url=Subquery(image_url))
        )

    @swagger_auto_schema(tags=["Core"])
    @method_decorator(cache_page(60 * 60 * 12))  # cache for 12 hrs
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class AttachmentsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = AttachmentSerializer
    parser_classes = [FormParser, JSONParser]
    throttle_classes = [EndpointThrottle]

    def get_queryset(self):
        image_url = AttachmentMedia.objects.filter(attachment_id=OuterRef("attachment_id")).values("image_url")[:1]
        return exclude_placeholder_dimensions(
            Attachments.objects.filter(is_leaf=True).annotate(image_url=Subquery(image_url))
        )

    @swagger_auto_schema(tags=["Core"])
    @method_decorator(cache_page(60 * 60 * 12))  # cache for 12 hrs
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

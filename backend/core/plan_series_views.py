from datetime import date

from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser
from rest_framework.response import Response

from .analytics.cache_utils import invalidate_user_analytics
from .api_throttle import EndpointThrottle
from .constants import SCENARIO_PLAN
from .models import PlanSeries, Workouts
from .plan_series_serializers import PlanSeriesSerializer


class PlanSeriesViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = PlanSeriesSerializer
    parser_classes = [FormParser, JSONParser]
    throttle_classes = [EndpointThrottle]
    lookup_field = "plan_series_id"

    def get_queryset(self):
        user = self.request.user
        qs = PlanSeries.objects.all() if user.is_staff else PlanSeries.objects.filter(user=user)
        return qs.order_by("-ta_created_at")

    def get_serializer(self, *args, **kwargs):
        kwargs.setdefault("context", self.get_serializer_context())
        return PlanSeriesSerializer(*args, **kwargs)

    @swagger_auto_schema(tags=["workout-planning"])
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(tags=["workout-planning"])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @swagger_auto_schema(tags=["workout-planning"])
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        invalidate_user_analytics(request.user.id)
        return Response(data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(tags=["workout-planning"])
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        invalidate_user_analytics(request.user.id)
        return Response(data)

    @swagger_auto_schema(tags=["workout-planning"])
    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(tags=["workout-planning"])
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        scope = (request.query_params.get("scope") or "future").strip().lower()
        if scope not in ("future", "all"):
            raise ValidationError({"scope": "Must be 'future' or 'all'."})

        filters = {"plan_group_id": instance.plan_series_id, "scenario": SCENARIO_PLAN}
        if scope == "future":
            filters["date_id__gte"] = date.today()

        deleted_count, _ = Workouts.objects.filter(**filters).delete()
        if scope == "all":
            instance.delete()
        else:
            remaining = Workouts.objects.filter(
                plan_group_id=instance.plan_series_id,
                scenario=SCENARIO_PLAN,
            ).exists()
            if not remaining:
                instance.delete()

        invalidate_user_analytics(request.user.id)
        return Response({"deleted_rows": deleted_count}, status=status.HTTP_200_OK)

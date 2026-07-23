from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.core.constants import TIME_FILTER_CURRENT
from backend.core.helpers import parse_optional_date_range

from .cache_utils import get_cached_analytics
from .crud.crud import (
    get_favourite_exercises,
    get_gym_weekdays,
    get_home_summary,
    get_rest_days,
    get_total_volume,
    get_total_volume_per_day,
    get_workout_sessions,
    get_workout_splits,
)
from .helpers import analytics_or_error


class UserRestDaysView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Analytics"])
    def get(self, request):
        user_id = request.user.id
        results = get_cached_analytics(
            user_id,
            "rest-days",
            {},
            lambda: get_rest_days(user_id),
        )
        return Response({"count": len(results), "results": results})


class FavouriteExercisesView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Analytics"],
        manual_parameters=[
            openapi.Parameter("start_date", openapi.IN_QUERY, type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            openapi.Parameter("end_date", openapi.IN_QUERY, type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
        ],
    )
    def get(self, request):
        user_id = request.user.id
        start_date_parsed, end_date_parsed = parse_optional_date_range(request.query_params)

        cache_params = {
            "start_date": start_date_parsed,
            "end_date": end_date_parsed,
        }
        results = analytics_or_error(
            lambda: get_cached_analytics(
                user_id,
                "favourite-exercises",
                cache_params,
                lambda: get_favourite_exercises(user_id, start_date=start_date_parsed, end_date=end_date_parsed),
            )
        )
        if isinstance(results, Response):
            return results
        for i, row in enumerate(results, 1):
            row["rank"] = i

        return Response({"results": results})


class TotalVolumeView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Analytics"],
        manual_parameters=[
            openapi.Parameter(
                "period",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                enum=list(TIME_FILTER_CURRENT),
            ),
            openapi.Parameter("start_date", openapi.IN_QUERY, type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            openapi.Parameter("end_date", openapi.IN_QUERY, type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            openapi.Parameter("parent_id", openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
        ],
    )
    def get(self, request):
        user_id = request.user.id
        period = (request.query_params.get("period") or "all").lower()
        if period not in TIME_FILTER_CURRENT:
            return Response(
                {"detail": f"period must be one of: {', '.join(TIME_FILTER_CURRENT)}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        start_date_parsed, end_date_parsed = parse_optional_date_range(request.query_params)

        parent_id_raw = request.query_params.get("parent_id")
        parent_id = None
        if parent_id_raw is not None and str(parent_id_raw).strip() != "":
            try:
                parent_id = int(parent_id_raw)
            except ValueError:
                return Response({"detail": "parent_id must be an integer."}, status=status.HTTP_400_BAD_REQUEST)

        cache_params = {
            "period": period,
            "start_date": start_date_parsed if period == "all" else None,
            "end_date": end_date_parsed if period == "all" else None,
            "parent_id": parent_id,
        }
        results = analytics_or_error(
            lambda: get_cached_analytics(
                user_id,
                "total-volume",
                cache_params,
                lambda: get_total_volume(
                    user_id,
                    parent_id=parent_id,
                    period=period,
                    start_date=start_date_parsed if period == "all" else None,
                    end_date=end_date_parsed if period == "all" else None,
                ),
            )
        )
        if isinstance(results, Response):
            return results
        for i, row in enumerate(results, 1):
            row["rank"] = i

        return Response({"results": results, "period": period})


class TotalVolumePerDayView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Analytics"],
        manual_parameters=[
            openapi.Parameter("exercise_id", openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
            openapi.Parameter("start_date", openapi.IN_QUERY, type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            openapi.Parameter("end_date", openapi.IN_QUERY, type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
        ],
    )
    def get(self, request):
        user_id = request.user.id
        exercise_id_raw = request.query_params.get("exercise_id")
        if not exercise_id_raw:
            return Response({"detail": "exercise_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            exercise_id = int(exercise_id_raw)
        except ValueError:
            return Response({"detail": "exercise_id must be an integer."}, status=status.HTTP_400_BAD_REQUEST)

        start_date_parsed, end_date_parsed = parse_optional_date_range(request.query_params)

        cache_params = {
            "exercise_id": exercise_id,
            "start_date": start_date_parsed,
            "end_date": end_date_parsed,
        }
        results = analytics_or_error(
            lambda: get_cached_analytics(
                user_id,
                "total-volume-daily",
                cache_params,
                lambda: get_total_volume_per_day(
                    user_id,
                    start_date=start_date_parsed,
                    end_date=end_date_parsed,
                    exercise_id=exercise_id,
                ),
            )
        )
        if isinstance(results, Response):
            return results

        return Response({"results": results})


class WorkoutSplitsView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Analytics"],
        manual_parameters=[
            openapi.Parameter("start_date", openapi.IN_QUERY, type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            openapi.Parameter("end_date", openapi.IN_QUERY, type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
        ],
    )
    def get(self, request):
        user_id = request.user.id
        start_date_parsed, end_date_parsed = parse_optional_date_range(request.query_params)

        cache_params = {
            "start_date": start_date_parsed,
            "end_date": end_date_parsed,
        }
        results = analytics_or_error(
            lambda: get_cached_analytics(
                user_id,
                "workout-splits",
                cache_params,
                lambda: get_workout_splits(user_id, start_date=start_date_parsed, end_date=end_date_parsed),
            )
        )
        if isinstance(results, Response):
            return results

        return Response({"results": results})


class GymWeekdaysView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Analytics"],
        manual_parameters=[
            openapi.Parameter("start_date", openapi.IN_QUERY, type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            openapi.Parameter("end_date", openapi.IN_QUERY, type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
        ],
    )
    def get(self, request):
        user_id = request.user.id
        start_date_parsed, end_date_parsed = parse_optional_date_range(request.query_params)

        cache_params = {
            "start_date": start_date_parsed,
            "end_date": end_date_parsed,
        }
        results = analytics_or_error(
            lambda: get_cached_analytics(
                user_id,
                "gym-weekdays",
                cache_params,
                lambda: get_gym_weekdays(user_id, start_date=start_date_parsed, end_date=end_date_parsed),
            )
        )
        if isinstance(results, Response):
            return results

        return Response({"results": results})


class WorkoutSessionsView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Analytics"],
        manual_parameters=[
            openapi.Parameter("start_date", openapi.IN_QUERY, type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            openapi.Parameter("end_date", openapi.IN_QUERY, type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
        ],
    )
    def get(self, request):
        user_id = request.user.id
        start_date_parsed, end_date_parsed = parse_optional_date_range(request.query_params)

        cache_params = {
            "start_date": start_date_parsed,
            "end_date": end_date_parsed,
        }
        payload = analytics_or_error(
            lambda: get_cached_analytics(
                user_id,
                "workout-sessions",
                cache_params,
                lambda: get_workout_sessions(user_id, start_date=start_date_parsed, end_date=end_date_parsed),
            )
        )
        if isinstance(payload, Response):
            return payload

        # Backward-compatible: older cache entries may still be a bare list.
        if isinstance(payload, list):
            return Response({"results": payload, "total": len(payload), "comparisons": {}})
        return Response(
            {
                "results": payload.get("results") or [],
                "total": payload.get("total") or len(payload.get("results") or []),
                "comparisons": payload.get("comparisons") or {},
            }
        )


class HomeSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Analytics"])
    def get(self, request):
        user_id = request.user.id
        summary = analytics_or_error(
            lambda: get_cached_analytics(
                user_id,
                "home-summary",
                {},
                lambda: get_home_summary(user_id),
            )
        )
        if isinstance(summary, Response):
            return summary

        return Response(summary)

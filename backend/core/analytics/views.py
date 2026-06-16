from django.utils.dateparse import parse_date
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .cache_utils import get_cached_analytics
from .crud.crud import (
    get_favourite_exercises,
    get_gym_weekdays,
    get_home_summary,
    get_rest_days,
    get_total_volume,
    get_total_volume_per_day,
    get_workout_splits,
)


def _parse_date_range(request):
    start_date = request.query_params.get("start_date")
    end_date = request.query_params.get("end_date")
    start_date_parsed = parse_date(start_date) if start_date else None
    end_date_parsed = parse_date(end_date) if end_date else None
    if start_date_parsed is not None and end_date_parsed is not None and start_date_parsed > end_date_parsed:
        return (
            None,
            None,
            Response(
                {"detail": "Make sure the start date is before the end date."},
                status=status.HTTP_400_BAD_REQUEST,
            ),
        )
    return start_date_parsed, end_date_parsed, None


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
        start_date_parsed, end_date_parsed, error = _parse_date_range(request)
        if error:
            return error

        cache_params = {
            "start_date": start_date_parsed,
            "end_date": end_date_parsed,
        }
        try:
            results = get_cached_analytics(
                user_id,
                "favourite-exercises",
                cache_params,
                lambda: get_favourite_exercises(user_id, start_date=start_date_parsed, end_date=end_date_parsed),
            )
            for i, row in enumerate(results, 1):
                row["rank"] = i
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"results": results})


class TotalVolumeView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Analytics"],
        manual_parameters=[
            openapi.Parameter("start_date", openapi.IN_QUERY, type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            openapi.Parameter("end_date", openapi.IN_QUERY, type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            openapi.Parameter("parent_id", openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
        ],
    )
    def get(self, request):
        user_id = request.user.id
        start_date_parsed, end_date_parsed, error = _parse_date_range(request)
        if error:
            return error

        parent_id_raw = request.query_params.get("parent_id")
        parent_id = None
        if parent_id_raw is not None and str(parent_id_raw).strip() != "":
            try:
                parent_id = int(parent_id_raw)
            except ValueError:
                return Response({"detail": "parent_id must be an integer."}, status=status.HTTP_400_BAD_REQUEST)

        cache_params = {
            "start_date": start_date_parsed,
            "end_date": end_date_parsed,
            "parent_id": parent_id,
        }
        try:
            results = get_cached_analytics(
                user_id,
                "total-volume",
                cache_params,
                lambda: get_total_volume(
                    user_id,
                    start_date=start_date_parsed,
                    end_date=end_date_parsed,
                    parent_id=parent_id,
                ),
            )
            for i, row in enumerate(results, 1):
                row["rank"] = i
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"results": results})


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

        start_date_parsed, end_date_parsed, error = _parse_date_range(request)
        if error:
            return error

        cache_params = {
            "exercise_id": exercise_id,
            "start_date": start_date_parsed,
            "end_date": end_date_parsed,
        }
        try:
            results = get_cached_analytics(
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
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        start_date_parsed, end_date_parsed, error = _parse_date_range(request)
        if error:
            return error

        cache_params = {
            "start_date": start_date_parsed,
            "end_date": end_date_parsed,
        }
        try:
            results = get_cached_analytics(
                user_id,
                "workout-splits",
                cache_params,
                lambda: get_workout_splits(user_id, start_date=start_date_parsed, end_date=end_date_parsed),
            )
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        start_date_parsed, end_date_parsed, error = _parse_date_range(request)
        if error:
            return error

        cache_params = {
            "start_date": start_date_parsed,
            "end_date": end_date_parsed,
        }
        try:
            results = get_cached_analytics(
                user_id,
                "gym-weekdays",
                cache_params,
                lambda: get_gym_weekdays(user_id, start_date=start_date_parsed, end_date=end_date_parsed),
            )
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"results": results})


class HomeSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Analytics"])
    def get(self, request):
        user_id = request.user.id
        try:
            summary = get_cached_analytics(
                user_id,
                "home-summary",
                {},
                lambda: get_home_summary(user_id),
            )
        except Exception as e:  # why do we throw a 500 error here directly and not let the server show any http code?
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(summary)

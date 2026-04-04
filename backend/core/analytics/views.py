from django.utils.dateparse import parse_date
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .crud.crud import get_favourite_exercises, get_rest_days, get_total_volume


class UserRestDaysView(APIView):
    @swagger_auto_schema(
        tags=["Analytics"],
    )
    def get(self, request):
        user_id = request.user.id
        results = get_rest_days(user_id)

        return Response(
            {
                "count": len(results),
                "results": results,
            },
        )


class FavouriteExercisesView(APIView):
    @swagger_auto_schema(
        tags=["Analytics"],
        manual_parameters=[
            openapi.Parameter(
                "start_date",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
                description="Start date (YYYY-MM-DD)",
            ),
            openapi.Parameter(
                "end_date",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
                description="End date (YYYY-MM-DD)",
            ),
        ],
    )
    def get(self, request):
        user_id = request.user.id
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        start_date_parsed = parse_date(start_date) if start_date else None
        end_date_parsed = parse_date(end_date) if end_date else None

        if start_date_parsed is not None and end_date_parsed is not None:
            if start_date_parsed > end_date_parsed:
                return Response(
                    {"detail": "Make sure the start date is before the end date."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        try:
            results = get_favourite_exercises(
                user_id,
                start_date=start_date_parsed,
                end_date=end_date_parsed,
            )
            for i, row in enumerate(results, 1):
                row["rank"] = i
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({"results": results})


class TotalVolumeView(APIView):
    @swagger_auto_schema(
        tags=["Analytics"],
        manual_parameters=[
            openapi.Parameter(
                "start_date",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
                description="Start date (YYYY-MM-DD)",
            ),
            openapi.Parameter(
                "end_date",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
                description="End date (YYYY-MM-DD)",
            ),
            openapi.Parameter(
                "parent_id",
                openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                format=openapi.FORMAT_INT64,
                description="ID of the exercise you want to drill down into.",
            ),
        ],
    )
    def get(self, request):
        user_id = request.user.id
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        parent_id = request.query_params.get("parent_id")

        start_date_parsed = parse_date(start_date) if start_date else None
        end_date_parsed = parse_date(end_date) if end_date else None

        if start_date_parsed is not None and end_date_parsed is not None:
            if start_date_parsed > end_date_parsed:
                return Response(
                    {"detail": "Make sure the start date is before the end date."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        try:
            results = get_total_volume(
                user_id,
                start_date=start_date_parsed,
                end_date=end_date_parsed,
                parent_id=parent_id,
            )
            for i, row in enumerate(results, 1):
                row["rank"] = i
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({"results": results})

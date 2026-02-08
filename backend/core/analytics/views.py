from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from .crud.crud import get_rest_days


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

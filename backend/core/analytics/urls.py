from django.urls import path

from .views import UserRestDaysView

urlpatterns = [
    path("v1/restdays", UserRestDaysView.as_view(), name="rest_days"),
]

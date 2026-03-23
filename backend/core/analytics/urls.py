from django.urls import path

from .views import FavouriteExercisesView, TotalVolumeView, UserRestDaysView

urlpatterns = [
    path("v1/rest-days", UserRestDaysView.as_view(), name="rest_days"),
    path("v1/favourite-exercises", FavouriteExercisesView.as_view(), name="favourite_exercises"),
    path("v1/total-volume", TotalVolumeView.as_view(), name="total-volume"),
]

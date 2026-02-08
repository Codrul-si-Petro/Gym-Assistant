from django.urls import path

from .views import FavouriteExercisesView, UserRestDaysView

urlpatterns = [
    path("v1/rest-days", UserRestDaysView.as_view(), name="rest_days"),
    path("v1/favourite-exercises", FavouriteExercisesView.as_view(), name="favourite_exercises"),
]

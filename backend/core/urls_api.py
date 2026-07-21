from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .plan_series_views import PlanSeriesViewSet
from .views import AttachmentsViewSet, EquipmentViewSet, ExercisesViewSet, MusclesViewSet, WorkoutsViewSet

router = DefaultRouter()
router.register(r"workouts", WorkoutsViewSet, basename="workouts")
router.register(r"plan-series", PlanSeriesViewSet, basename="plan-series")
router.register(r"exercises", ExercisesViewSet, basename="exercises")
router.register(r"attachments", AttachmentsViewSet, basename="attachments")
router.register(r"muscles", MusclesViewSet, basename="muscles")
router.register(r"equipment", EquipmentViewSet, basename="equipment")

urlpatterns = [
    path("", include(router.urls)),
]

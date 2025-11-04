from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WorkoutsViewSet, ExercisesViewSet

router = DefaultRouter()
router.register(r'workouts', WorkoutsViewSet, basename='workouts')
router.register(r'exercises', ExercisesViewSet, basename='exercises')

urlpatterns = [
    path('', include(router.urls)),
]

from django.db import connection as conn
from rest_framework import viewsets
from .models import Workouts, Exercises
from .serializers import WorkoutSerializer, ExercisesSerializer


class WorkoutsViewSet(viewsets.ModelViewSet):
    queryset = Workouts.objects.all()
    serializer_class = WorkoutSerializer

class ExercisesViewSet(viewsets.ModelViewSet):
    queryset = Exercises.objects.all()
    serializer_class = ExercisesSerializer

    def set_search_path(self):
        with conn.cursor() as cursor:
            cursor.execute('SET search_path TO core, public;')

    def create(self, request, *args, **kwargs):
        self.set_search_path()
        return super().create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        self.set_search_path()
        return super().list(request, *args, **kwargs)

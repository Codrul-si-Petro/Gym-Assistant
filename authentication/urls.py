from django.urls import path
from .views import LoginSuccessView

urlpatterns = [
    path('login/', LoginSuccessView, name='login-success'),
]

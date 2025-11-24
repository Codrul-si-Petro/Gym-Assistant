from django.urls import path
from .views import login_success_view

urlpatterns = [
    path('login-success/', login_success_view, name='login-success'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('login-success/', views.login_success, name='login-success'),
]

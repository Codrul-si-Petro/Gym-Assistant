from django.urls import path
from .views import LoginSuccessView

urlpatterns = [
    path('login-success/', LoginSuccessView.as_view(), name='login_success'),
]

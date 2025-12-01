from django.urls import path
from .views import (
        login_success_view,
        login_page_view
        )

urlpatterns = [
    path('login-success/', login_success_view, name='login_success'),
    path('login/', login_page_view, name='login')
]

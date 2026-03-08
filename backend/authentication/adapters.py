# backend/authentication/adapters.py
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken

class JWTRedirectAdapter(DefaultSocialAccountAdapter):
    def get_login_redirect_url(self, request):
        """
        Called after any login (social or regular). Issue JWTs for social users.
        """
        user = request.user
        frontend_url = settings.FRONTEND_URL.rstrip("/")
        
        if user.is_authenticated:
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            return f"{frontend_url}/homepage.html?access={access_token}&refresh={refresh_token}"
        
        # fallback to default
        return super().get_login_redirect_url(request)


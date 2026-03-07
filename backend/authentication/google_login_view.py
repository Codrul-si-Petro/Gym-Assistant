from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.shortcuts import redirect
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from urllib.parse import urlencode

@api_view(["GET"])
@permission_classes([AllowAny])
def google_oauth_jwt_redirect(request):
    """
    This view is the callback URL for Google OAuth.
    If the user is authenticated, return JWTs.
    Otherwise redirect to frontend login.
    """
    user = request.user
    if user.is_authenticated:
        # Issue JWTs
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token) # TODO: find out why this branch isnt taken into consideration with the new frontend
        refresh_token = str(refresh)

        # Redirect to frontend home
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5500")
        params = urlencode({"access": access_token, "refresh": refresh_token})
        redirect_url = f"{frontend_url}/homepage.html?{params}"
        print(settings.FRONTEND_URL)
        print(f"REDIRECTING TO: {redirect_url}")
        return redirect(redirect_url)
    
    # Not logged in: redirect to login
    print(f"LOGIN FAILED REDIRECTING TO login html")
    return redirect(f"{settings.FRONTEND_URL}/pages/login.html")

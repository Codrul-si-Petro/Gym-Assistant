from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken


def get_jwt_login_redirect_url(request):
    """
    Build frontend redirect URL with JWT. Used after login (including social).
    Returns None if user not authenticated or FRONTEND_URL missing.
    """
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return None
    frontend_url = getattr(settings, "FRONTEND_URL", "").rstrip("/")
    if not frontend_url:
        return None
    refresh = RefreshToken.for_user(request.user)
    access = str(refresh.access_token)
    ref = str(refresh)
    return f"{frontend_url}/index.html?access={access}&refresh={ref}"


class JWTAccountAdapter(DefaultAccountAdapter):
    """
    Account adapter: JWT redirect after login/signup. No MailerSend; uses Django default email.
    """

    def get_login_redirect_url(self, request):
        url = get_jwt_login_redirect_url(request)
        if url:
            return url
        return super().get_login_redirect_url(request)

    def get_signup_redirect_url(self, request):
        return self.get_login_redirect_url(request)


class JWTRedirectAdapter(DefaultSocialAccountAdapter):
    """Social adapter: redirect with JWT when applicable."""

    def get_login_redirect_url(self, request):
        url = get_jwt_login_redirect_url(request)
        if url:
            return url
        frontend_url = getattr(settings, "FRONTEND_URL", "").rstrip("/") or ""
        return f"{frontend_url}/pages/auth/login.html"

    def get_signup_redirect_url(self, request):
        return self.get_login_redirect_url(request)

from django.conf import settings
from django.http import HttpResponseNotFound
from django.shortcuts import redirect


def homepageView(request):
    return redirect(f"{settings.FRONTEND_URL.rstrip('/')}/index.html")


def sentry_debug(request):
    """Deliberate crash to verify Sentry captures exceptions. DEBUG-only."""
    if not settings.DEBUG:
        return HttpResponseNotFound()
    _ = 1 / 0

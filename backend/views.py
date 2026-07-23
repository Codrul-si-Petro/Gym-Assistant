from django.conf import settings
from django.db import connection
from django.http import HttpResponseNotFound, JsonResponse
from django.shortcuts import redirect


def homepageView(request):
    return redirect(f"{settings.FRONTEND_URL.rstrip('/')}/index.html")


def health(request):
    """Cheap liveness/readiness check for uptime monitors. No auth, no DRF."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({"status": "ok"})
    except Exception:
        return JsonResponse({"status": "error"}, status=503)


def sentry_debug(request):
    """Deliberate crash to verify Sentry captures exceptions. DEBUG-only."""
    if not settings.DEBUG:
        return HttpResponseNotFound()
    _ = 1 / 0

from django.conf import settings
from django.shortcuts import redirect


def homepageView(request):
    return redirect(f"{settings.FRONTEND_URL.rstrip('/')}/index.html")

from functools import wraps

from django.shortcuts import redirect


def staff_sso_required(view_func):
    """Require a staff session; otherwise stash the path and send the user to Google SSO."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            return view_func(request, *args, **kwargs)
        request.session["post_login_redirect"] = request.get_full_path()
        return redirect("/social/google/login/")

    return _wrapped

"""Shared helpers for analytics views."""

import logging
from collections.abc import Callable
from typing import TypeVar

from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)

T = TypeVar("T")


def analytics_or_error(fetch_fn: Callable[[], T]) -> T | Response:
    """Run an analytics fetch; return a generic 500 Response on unexpected errors.

    Does not leak exception text to clients — the traceback stays in server logs
    (and Sentry when SENTRY_DSN is configured). Callers should check
    ``isinstance(result, Response)`` before using the value.
    """
    try:
        return fetch_fn()
    except Exception as exc:
        logger.exception("Analytics query failed")
        try:
            import sentry_sdk

            sentry_sdk.capture_exception(exc)
        except Exception:
            pass
        return Response(
            {"detail": "An unexpected error occurred while loading analytics."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

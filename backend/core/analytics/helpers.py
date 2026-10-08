"""Shared helpers for analytics views."""

import logging
from collections.abc import Callable
from datetime import date, timedelta
from typing import TypeVar

from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)

T = TypeVar("T")


def query_analytics(fetch_fn: Callable[[], T]) -> T | Response:
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


def get_period_bounds(today: date, unit: str) -> dict[str, date]:
    match unit:
        case "week":
            cur_start = today - timedelta(days=today.isoweekday() - 1)
            full_end = cur_start + timedelta(days=6)

        case "month":
            cur_start = today.replace(day=1)
            next_month = cur_start.replace(day=28) + timedelta(days=4)
            full_end = next_month.replace(day=1) - timedelta(days=1)

        case "year":
            cur_start = today.replace(month=1, day=1)
            full_end = today.replace(month=12, day=31)

        case _:
            raise ValueError(f"Unsupported period unit: {unit}")

    cur_end = today
    prev_end = cur_start - timedelta(days=1)

    match unit:
        case "week":
            prev_start = prev_end - timedelta(days=6)

        case "month":
            prev_start = prev_end.replace(day=1)

        case "year":
            prev_start = cur_start.replace(year=cur_start.year - 1)
            prev_end = prev_start.replace(month=12, day=31)

    return {
        "cur_start": cur_start,
        "cur_end": cur_end,
        "prev_start": prev_start,
        "prev_end": prev_end,
        "full_end": full_end,
    }

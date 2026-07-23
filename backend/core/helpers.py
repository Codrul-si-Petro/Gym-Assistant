"""Shared helpers for the core app."""

from datetime import date

from django.utils.dateparse import parse_date
from rest_framework.exceptions import ValidationError


def parse_optional_date_range(params) -> tuple[date | None, date | None]:
    """Parse optional ISO start_date/end_date from a query-param mapping.

    Raises ValidationError when a provided value is not an ISO date, or when
    start_date is after end_date.
    """
    start_raw = params.get("start_date")
    end_raw = params.get("end_date")
    start_date = parse_date(start_raw) if start_raw else None
    end_date = parse_date(end_raw) if end_raw else None

    if start_raw and start_date is None:
        raise ValidationError({"start_date": "Must be an ISO date (YYYY-MM-DD)."})
    if end_raw and end_date is None:
        raise ValidationError({"end_date": "Must be an ISO date (YYYY-MM-DD)."})
    if start_date and end_date and start_date > end_date:
        raise ValidationError({"detail": "Make sure the start date is before the end date."})

    return start_date, end_date

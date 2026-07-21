"""Expand plan recurrence rules into concrete calendar dates."""

from datetime import date, timedelta

WEEKDAY_CODES = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")
WEEKDAY_TO_ISO = {code: idx for idx, code in enumerate(WEEKDAY_CODES)}

MAX_PLAN_SPAN_DAYS = 365
MAX_OCCURRENCES = 366


class RecurrenceError(ValueError):
    """Invalid recurrence parameters."""


def _validate_span(start_date: date, end_date: date) -> None:
    if end_date < start_date:
        raise RecurrenceError("End date must be on or after start date.")
    if (end_date - start_date).days > MAX_PLAN_SPAN_DAYS:
        raise RecurrenceError(f"Plan span cannot exceed {MAX_PLAN_SPAN_DAYS} days.")


def expand_recurrence(
    start_date: date,
    end_date: date,
    recurrence_type: str,
    weekdays: list[str] | None = None,
    interval_days: int | None = None,
) -> list[date]:
    """Return sorted unique occurrence dates for a recurrence rule."""
    _validate_span(start_date, end_date)

    if recurrence_type == "once":
        return [start_date]

    if recurrence_type == "weekly":
        if not weekdays:
            raise RecurrenceError("Select at least one weekday for a weekly plan.")
        invalid = [d for d in weekdays if d not in WEEKDAY_TO_ISO]
        if invalid:
            raise RecurrenceError(f"Invalid weekday codes: {', '.join(invalid)}")
        target_weekdays = {WEEKDAY_TO_ISO[d] for d in weekdays}
        dates: list[date] = []
        current = start_date
        while current <= end_date:
            if current.weekday() in target_weekdays:
                dates.append(current)
            current += timedelta(days=1)
        if not dates:
            raise RecurrenceError("No dates match the selected weekdays in this range.")
        if len(dates) > MAX_OCCURRENCES:
            raise RecurrenceError(f"Plan generates too many dates (max {MAX_OCCURRENCES}).")
        return dates

    if recurrence_type == "interval":
        if interval_days is None or interval_days < 1:
            raise RecurrenceError("Interval must be at least 1 day.")
        dates = []
        current = start_date
        while current <= end_date:
            dates.append(current)
            current += timedelta(days=interval_days)
        if len(dates) > MAX_OCCURRENCES:
            raise RecurrenceError(f"Plan generates too many dates (max {MAX_OCCURRENCES}).")
        return dates

    raise RecurrenceError(f"Unknown recurrence type: {recurrence_type}")

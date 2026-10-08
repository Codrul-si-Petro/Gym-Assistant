"""Expand plan recurrence rules into concrete calendar dates."""

from datetime import date, timedelta

WEEKDAY_CODES = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")
WEEKDAY_TO_ISO = {code: idx for idx, code in enumerate(WEEKDAY_CODES)}

MAX_PLAN_SPAN_DAYS = 365
MAX_OCCURRENCES = 366


# TODO: make a module with custom errors and remove garbage like this
class RecurrenceError(ValueError):
    """Invalid recurrence parameters."""


# TODO: also make garbage like this a helper somewhere
def validate_span(start_date: date, end_date: date) -> None:
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
    specific_dates: list[date] | None = None,
) -> list[date]:
    """Return sorted unique occurrence dates for a recurrence rule."""

    match recurrence_type:
        case "dates":
            if not specific_dates:
                raise RecurrenceError("Select at least one date.")

            dates = sorted(set(specific_dates))
            validate_span(dates[0], dates[-1])

        case "once":
            validate_span(start_date, end_date)
            dates = [start_date]

        case "weekly":
            validate_span(start_date, end_date)

            if not weekdays:
                raise RecurrenceError("Select at least one weekday for a weekly plan.")

            invalid = [d for d in weekdays if d not in WEEKDAY_TO_ISO]
            if invalid:
                raise RecurrenceError(f"Invalid weekday codes: {', '.join(invalid)}")

            target_weekdays = {WEEKDAY_TO_ISO[d] for d in weekdays}
            dates = [
                start_date + timedelta(days=offset)
                for offset in range((end_date - start_date).days + 1)
                if (start_date + timedelta(days=offset)).weekday() in target_weekdays
            ]

            if not dates:
                raise RecurrenceError("No dates match the selected weekdays in this range.")

        case "interval":
            validate_span(start_date, end_date)

            if interval_days is None or interval_days < 1:
                raise RecurrenceError("Interval must be at least 1 day.")

            dates = []
            current = start_date
            while current <= end_date:
                dates.append(current)
                current += timedelta(days=interval_days)

        case _:
            raise RecurrenceError(f"Unknown recurrence type: {recurrence_type}")

    if len(dates) > MAX_OCCURRENCES:
        raise RecurrenceError(f"Plan generates too many dates (max {MAX_OCCURRENCES}).")

    return dates

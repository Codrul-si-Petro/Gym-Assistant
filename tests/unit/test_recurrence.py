"""Tests for recurrence date expansion."""

from datetime import date

import pytest

from backend.core.recurrence import RecurrenceError, expand_recurrence


def test_expand_once():
    dates = expand_recurrence(date(2026, 7, 22), date(2026, 7, 22), "once")
    assert dates == [date(2026, 7, 22)]


def test_expand_weekly():
    dates = expand_recurrence(
        date(2026, 7, 20),
        date(2026, 7, 31),
        "weekly",
        weekdays=["MON", "WED", "FRI"],
    )
    assert date(2026, 7, 20) in dates
    assert date(2026, 7, 22) in dates
    assert all(d.weekday() in (0, 2, 4) for d in dates)


def test_expand_interval():
    dates = expand_recurrence(date(2026, 7, 1), date(2026, 7, 10), "interval", interval_days=3)
    assert dates == [date(2026, 7, 1), date(2026, 7, 4), date(2026, 7, 7), date(2026, 7, 10)]


def test_expand_rejects_long_span():
    with pytest.raises(RecurrenceError):
        expand_recurrence(date(2026, 1, 1), date(2027, 2, 1), "interval", interval_days=7)

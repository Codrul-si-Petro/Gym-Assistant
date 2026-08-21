"""Unit tests for shared optional date-range parsing."""

import pytest
from rest_framework.exceptions import ValidationError

from backend.core.helpers import parse_optional_date_range


def test_parse_optional_date_range_empty():
    assert parse_optional_date_range({}) == (None, None)


def test_parse_optional_date_range_valid():
    start, end = parse_optional_date_range({"start_date": "2025-01-01", "end_date": "2025-01-31"})
    assert start.isoformat() == "2025-01-01"
    assert end.isoformat() == "2025-01-31"


def test_parse_optional_date_range_rejects_inverted_range():
    with pytest.raises(ValidationError):
        parse_optional_date_range({"start_date": "2025-12-01", "end_date": "2025-01-01"})


def test_parse_optional_date_range_rejects_bad_iso():
    with pytest.raises(ValidationError):
        parse_optional_date_range({"start_date": "not-a-date"})

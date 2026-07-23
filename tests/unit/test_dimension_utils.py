"""Unit tests for placeholder dimension exclusion."""

import pytest

from backend.core.constants import PLACEHOLDER_DIMENSION_ID, PLACEHOLDER_DIMENSION_NAME
from backend.core.dimension_utils import exclude_placeholder_dimensions
from backend.core.models import Exercises


@pytest.mark.django_db
def test_exclude_placeholder_dimensions_drops_sentinel_exercise_rows():
    qs = Exercises.objects.all()
    if (
        not qs.filter(exercise_id=PLACEHOLDER_DIMENSION_ID).exists()
        and not qs.filter(exercise_name=PLACEHOLDER_DIMENSION_NAME).exists()
    ):
        pytest.skip("No placeholder exercise row seeded in this database")

    filtered = exclude_placeholder_dimensions(qs)
    assert not filtered.filter(exercise_id=PLACEHOLDER_DIMENSION_ID).exists()
    assert not filtered.filter(exercise_name=PLACEHOLDER_DIMENSION_NAME).exists()

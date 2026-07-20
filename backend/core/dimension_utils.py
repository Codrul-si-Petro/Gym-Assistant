from .constants import PLACEHOLDER_DIMENSION_ID, PLACEHOLDER_DIMENSION_NAME

_NAME_FIELD_BY_MODEL = {
    "Exercises": "exercise_name",
    "Attachments": "attachment_name",
    "Equipment": "equipment_name",
    "Muscles": "muscle_name",
}


def exclude_placeholder_dimensions(queryset):
    """Drop sentinel None/-1 rows used for optional workout FK defaults."""
    model_name = queryset.model.__name__
    pk_field = queryset.model._meta.pk.name
    qs = queryset.exclude(**{pk_field: PLACEHOLDER_DIMENSION_ID})

    name_field = _NAME_FIELD_BY_MODEL.get(model_name)
    if name_field:
        qs = qs.exclude(**{name_field: PLACEHOLDER_DIMENSION_NAME})

    return qs

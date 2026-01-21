from django.core import checks
from django.db import models


class DateForeignKey(models.ForeignKey):
    """
    A ForeignKey variant that stores a DATE column instead of an integer because Django's
    ORM is horrible and does not have this implemented.
    Use only when the referenced PK/to_field is a DateField.
    """

    def __init__(self, to, to_field=None, **kwargs):
        super().__init__(to, to_field=to_field, **kwargs)

    def db_type(self, connection):
        # Force PostgreSQL to use DATE as column type
        return "date"

    def get_db_prep_value(self, value, connection, prepared=False):
        if not value:
            return None
        return value

    def rel_db_type(self, connection):
        return "date"

    def check(self, **kwargs):
        errors = super().check(**kwargs)
        # Validate target_field here safely
        target_field = self.target_field
        if target_field.get_internal_type() != "DateField":
            errors.append(
                checks.Error(
                    f"DateForeignKey references a non-DateField: {target_field.name}",
                    obj=self,
                    id="fields.E001",
                )
            )
        return errors

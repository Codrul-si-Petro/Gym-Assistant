"""Stub models for dimension tables managed by dbt and Django.

These models exist only to allow SQLAlchemy to resolve foreign key references
in fact_workouts. They are NOT tracked by Alembic - the actual tables are
managed by dbt seeds/transformations or Django migrations.
"""

from core.fact_workouts import CoreTable
from sqlalchemy import BIGINT, DATE, INTEGER, Column, MetaData
from sqlmodel import Field, SQLModel

# Separate metadata for public schema (Django-managed tables)
public_metadata = MetaData(schema="public")


class DimCalendar(CoreTable, table=True):  # type: ignore[call-arg]
    """Stub model for dim_calendar - managed by dbt, not Alembic."""

    __tablename__ = "dim_calendar"

    date_id: int = Field(sa_column=Column(DATE, primary_key=True))


class DimExercises(CoreTable, table=True):  # type: ignore[call-arg]
    """Stub model for dim_exercises - managed by dbt, not Alembic."""

    __tablename__ = "dim_exercises"

    exercise_id: int = Field(sa_column=Column(INTEGER, primary_key=True))


class DimAttachments(CoreTable, table=True):  # type: ignore[call-arg]
    """Stub model for dim_attachments - managed by dbt, not Alembic."""

    __tablename__ = "dim_attachments"

    attachment_id: int = Field(sa_column=Column(INTEGER, primary_key=True))


class DimEquipment(CoreTable, table=True):  # type: ignore[call-arg]
    """Stub model for dim_equipment - managed by dbt, not Alembic."""

    __tablename__ = "dim_equipment"

    equipment_id: int = Field(sa_column=Column(INTEGER, primary_key=True))


class AuthenticationUser(SQLModel, table=True):
    """Stub model for authentication_user - managed by Django, not Alembic."""

    __tablename__ = "authentication_user"
    __table_args__ = {"schema": "public"}
    metadata = CoreTable.metadata  # Use same metadata so foreign keys can resolve

    id: int = Field(sa_column=Column(BIGINT, primary_key=True))

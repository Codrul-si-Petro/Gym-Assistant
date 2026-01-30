from datetime import date, datetime
from typing import ClassVar

from sqlalchemy import DATE, INTEGER, NUMERIC, SMALLINT, TIMESTAMP, VARCHAR, Column, ForeignKey, Index, MetaData, text
from sqlalchemy.dialects.postgresql import TEXT
from sqlmodel import Field, SQLModel

"""
For now this will only control the fact table as we are using a dbt seed approach to keep track of dimensions.
"""


class CoreTable(SQLModel):
    __abstract__ = True
    metadata = MetaData(schema="core")


class FactWorkouts(CoreTable, table=True):
    __tablename__: ClassVar[str] = "fact_workouts"
    __table_args__: tuple[Index, Index, dict[str, str]] = (
        Index("ix_fact_workout_user_date", "user_id", "date_id"),
        Index("ix_fact_workout_user_id", "user_id"),
        {"comment": "Fact table where users log their workouts."},
    )
    workout_id: int = Field(sa_column=Column(INTEGER, primary_key=True, comment="Unique workout identifier"))
    user_id: int = Field(
        sa_column=Column(INTEGER, ForeignKey("public.authentication_user.id", ondelete="CASCADE"), nullable=False)
    )
    workout_number: int = Field(sa_column=Column(INTEGER, nullable=False))
    date_id: date = Field(sa_column=Column(DATE, ForeignKey("core.dim_calendar.date_id"), nullable=False))
    exercise_id: int = Field(
        sa_column=Column(INTEGER, ForeignKey("core.dim_exercises.exercise_id"), nullable=False),
    )
    set_number: int = Field(sa_column=Column(SMALLINT, nullable=False))
    repetitions: int = Field(sa_column=Column(SMALLINT, nullable=False))
    load: float = Field(sa_column=Column(NUMERIC, nullable=False))
    unit: str = Field(sa_column=Column(TEXT, nullable=False, server_default="'KG'"))
    equipment_id: int = Field(sa_column=Column(INTEGER, ForeignKey("core.dim_equipment.equipment_id"), nullable=False))
    attachment_id: int = Field(
        sa_column=Column(INTEGER, ForeignKey("core.dim_attachments.attachment_id"), nullable=False)
    )
    set_type: str = Field(sa_column=Column(VARCHAR(255), nullable=False, server_default="'Working set'"))
    comments: str = Field(sa_column=Column(TEXT, nullable=False, server_default="'N/A'"))
    workout_split: str = Field(sa_column=Column(TEXT, nullable=False))
    laterality: str = Field(sa_column=Column(VARCHAR(255), nullable=False, server_default="'Bilateral'"))

    ta_created_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=text("now()"),
            nullable=False,
        )
    )
    ta_updated_at: datetime | None = Field(default=None, sa_column=Column(TIMESTAMP(timezone=True), nullable=True))

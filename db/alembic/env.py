"""Alembic environment configuration for multi-schema setup."""

import os
from logging.config import fileConfig

from alembic import context

# Import dimension stubs first so foreign keys can be resolved
from core import dimensions  # noqa: F401
from core.fact_workouts import CoreTable
from dotenv import load_dotenv
from sqlalchemy import create_engine, pool, text

# Load environment variables
load_dotenv()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Get database URL from environment
DATABASE_URL: str = os.getenv("DATABASE_URL_NO_POOLER", "")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL_NO_POOLER environment variable is required")

# Only track tables in the core schema (currently just fact_workouts)
# All stub models (dimensions and AuthenticationUser) use CoreTable.metadata
# so foreign keys can resolve, but include_object filter will ignore them
target_metadata = CoreTable.metadata


def include_object(object, name, type_, reflected, compare_to):
    """Filter to only track fact_workouts table, ignore dimension stubs."""
    if type_ == "table":
        # Only track fact_workouts, ignore dimension tables (managed by dbt)
        return name == "fact_workouts"
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Generates SQL scripts without connecting to the database.
    Useful for reviewing SQL before execution or when direct connection isn't possible.
    Only tracks tables in the 'core' schema (specifically fact_workouts).
    """
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Connects to the database and executes migrations directly.
    Only tracks tables in the 'core' schema (specifically fact_workouts).
    """
    connectable = create_engine(DATABASE_URL, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        # Create core schema if it doesn't exist
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS core"))
        connection.commit()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema="public",
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

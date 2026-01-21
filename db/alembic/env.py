"""Alembic environment configuration for multi-schema setup."""

import os
from logging.config import fileConfig

from alembic import context
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


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=None,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = create_engine(DATABASE_URL, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        # Create schemas if they don't exist
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS core"))
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS seeds"))
        connection.commit()

        context.configure(
            connection=connection,
            target_metadata=None,
            version_table_schema="public",
            include_schemas=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

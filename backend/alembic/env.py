"""Alembic environment configuration."""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool
from finlite.config import get_settings
from finlite.infrastructure.persistence.sqlalchemy.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

TARGET_METADATA = Base.metadata


def run_migrations_offline() -> None:
    settings = get_settings()
    url = settings.database_url
    context.configure(url=url, target_metadata=TARGET_METADATA, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    settings = get_settings()
    
    # Create engine directly
    connectable = create_engine(
        settings.database_url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=TARGET_METADATA)

        with context.begin_transaction():
            context.run_migrations()


def run_migrations() -> None:
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()


run_migrations()

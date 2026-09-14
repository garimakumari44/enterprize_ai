
"""
Alembic migration environment.

This module configures Alembic to use the application's SQLAlchemy
Base metadata and database URL.

All ORM models are registered through:

    app.db.models

so that Alembic can correctly detect all tables and relationships.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.db.base import Base

# IMPORTANT:
# Import the complete ORM model registry so every SQLAlchemy model
# is registered with Base.metadata before Alembic compares schemas.
import app.db.models


# ============================================================
# Alembic configuration
# ============================================================

config = context.config


# ============================================================
# Database URL
# ============================================================

# Use the application's configured DATABASE_URL instead of
# relying on the value inside alembic.ini.
config.set_main_option(
    "sqlalchemy.url",
    settings.DATABASE_URL,
)


# ============================================================
# Logging
# ============================================================

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# ============================================================
# SQLAlchemy metadata
# ============================================================

# app.db.models imports all ORM models and registers their
# tables with the canonical Base.metadata.
target_metadata = Base.metadata


# ============================================================
# Offline migrations
# ============================================================

def run_migrations_offline() -> None:
    """
    Run migrations without creating a live database connection.
    """

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
        dialect_opts={
            "paramstyle": "named",
        },
    )

    with context.begin_transaction():
        context.run_migrations()


# ============================================================
# Online migrations
# ============================================================

def run_migrations_online() -> None:
    """
    Run migrations using a live database connection.
    """

    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# ============================================================
# Migration entry point
# ============================================================

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()


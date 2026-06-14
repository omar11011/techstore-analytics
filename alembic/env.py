"""
Alembic environment configuration for TechStore Analytics.

This module configures Alembic to work with the SQLAlchemy models defined
in the ``app.models`` package.  It supports both **offline** migration
(emit SQL scripts without a database connection) and **online** migration
(run migrations against a live database).

The ``DATABASE_URL`` is read from the environment variable of the same
name, falling back to the URL defined in ``alembic.ini``.
"""

import os
import logging
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# ---------------------------------------------------------------------------
# Alembic Config object – provides access to values in alembic.ini
# ---------------------------------------------------------------------------
config = context.config

# ---------------------------------------------------------------------------
# Interpret the config file for Python logging.
# ---------------------------------------------------------------------------
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Import Base and ALL model classes so they register with Base.metadata.
#
# This is critical: if a model is not imported here, Alembic's autogenerate
# will not detect it and will not produce the corresponding table operations.
# ---------------------------------------------------------------------------
from app.database.config import Base  # noqa: E402
from app.models import (  # noqa: E402
    Customer,
    Category,
    Supplier,
    Product,
    Store,
    Inventory,
    Order,
    OrderItem,
    Payment,
    Shipment,
)

# ---------------------------------------------------------------------------
# Target metadata for autogenerate support
# ---------------------------------------------------------------------------
target_metadata = Base.metadata

# ---------------------------------------------------------------------------
# Override sqlalchemy.url with the DATABASE_URL environment variable
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)


def get_url() -> str:
    """Return the database URL from the environment or the config file.

    The ``DATABASE_URL`` environment variable takes precedence.  If it is
    not set, the ``sqlalchemy.url`` value from ``alembic.ini`` is used.

    Returns:
        str: A fully-resolved database connection string.
    """
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        # Ensure the psycopg2 dialect is used for PostgreSQL URLs.
        if env_url.startswith("postgres://"):
            env_url = env_url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif env_url.startswith("postgresql://") and "+" not in env_url.split("://")[1][:20]:
            env_url = env_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return env_url
    return config.get_main_option("sqlalchemy.url", "")


# =========================================================================
# Offline migration
# =========================================================================

def run_migrations_offline() -> None:
    """Run migrations in *offline* mode.

    This configures the context with just a URL and not an Engine.  Calls
    to ``context.execute()`` emit the given string to the script output.

    The generated SQL script can be reviewed before being applied to a
    production database, or used when direct database access is not
    available.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# =========================================================================
# Online migration
# =========================================================================

def run_migrations_online() -> None:
    """Run migrations in *online* mode.

    In this scenario we create an Engine and associate a connection with
    the context, then run the migrations within a transaction.
    """
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# =========================================================================
# Entry point
# =========================================================================

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

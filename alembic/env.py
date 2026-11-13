
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
from backend.app.models import *
from backend.app.db.database import Base, get_migration_database_url
from backend.app.core.config import settings
config = context.config

# Resolve migration database URL: prefers MIGRATION_DATABASE_URL (leadvoix_migrator role),
# falling back to DATABASE_URL in development.
migration_url = get_migration_database_url()
config.set_main_option("sqlalchemy.url", migration_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_context_configure_kwargs(connection=None, url=None) -> dict:
    """
    Constructs context.configure arguments.
    Enforces include_schemas=True.
    When running against PostgreSQL, explicitly pins alembic_version table
    to schema 'public' so that the dedicated leadvoix_migrator role can manage
    the version history without requiring schema-wide DDL rights on public.
    """
    kwargs = {
        "target_metadata": target_metadata,
        "include_schemas": True,
    }
    is_pg = False
    if connection is not None:
        kwargs["connection"] = connection
        dialect = getattr(connection, "dialect", None)
        is_pg = getattr(dialect, "name", "") == "postgresql"
    elif url is not None:
        kwargs["url"] = url
        kwargs["literal_binds"] = True
        kwargs["dialect_opts"] = {"paramstyle": "named"}
        is_pg = "postgres" in str(url).lower()

    if is_pg:
        kwargs["version_table"] = "alembic_version"
        kwargs["version_table_schema"] = "public"

    return kwargs


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url") or get_migration_database_url()
    configure_kwargs = get_context_configure_kwargs(url=url)
    context.configure(**configure_kwargs)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    section = config.get_section(config.config_ini_section, {}) or {}
    section["sqlalchemy.url"] = get_migration_database_url()

    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        configure_kwargs = get_context_configure_kwargs(connection=connection)
        context.configure(**configure_kwargs)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

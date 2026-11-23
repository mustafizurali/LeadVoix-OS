import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from backend.app.core.config import settings

def get_db_url() -> str:
    url = getattr(settings, "DATABASE_URL", "")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


_db_url = get_db_url()
_connect_args = {}
if "pg8000" in _db_url:
    _connect_args["timeout"] = 10
elif "postgresql" in _db_url:
    _connect_args["connect_timeout"] = 10

engine = create_engine(
    _db_url,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args=_connect_args,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_migration_database_url() -> str:
    """
    Returns the database URL for running Alembic migrations.
    Prioritizes MIGRATION_DATABASE_URL (or ALEMBIC_DATABASE_URL) for the dedicated
    leadvoix_migrator connection, falling back to settings.DATABASE_URL in development.
    Normalizes 'postgres://' to 'postgresql://' for SQLAlchemy 1.4+ compatibility.
    """
    url = (
        os.getenv("MIGRATION_DATABASE_URL")
        or os.getenv("ALEMBIC_DATABASE_URL")
        or getattr(settings, "DATABASE_URL", "")
    )
    if not url or not url.strip():
        raise RuntimeError(
            "Configuration error: Neither MIGRATION_DATABASE_URL nor DATABASE_URL is set."
        )
    url = url.strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def get_context_configure_kwargs(target_metadata=None, connection=None, url=None) -> dict:
    """
    Constructs context.configure arguments for Alembic.
    Enforces include_schemas=True.
    When running against PostgreSQL, explicitly pins alembic_version table
    to schema 'public' so that the dedicated leadvoix_migrator role can manage
    the version history without requiring schema-wide DDL rights on public.
    """
    kwargs = {
        "include_schemas": True,
    }
    if target_metadata is not None:
        kwargs["target_metadata"] = target_metadata

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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

        # Import all models so Alembic can detect them
from backend.app.models import *

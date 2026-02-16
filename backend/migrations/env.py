"""Alembic environment configuration for TREFF Post-Generator.

Supports both local SQLite and Turso (hosted SQLite) databases.
Uses synchronous SQLite driver for migrations (not async aiosqlite).
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context

# Ensure the backend directory is in sys.path so 'app' can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.core.database import Base

# Import all models so their metadata is registered with Base
import app.models  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata from our Base for autogenerate support
target_metadata = Base.metadata

# Build synchronous database URL for migrations
# (Alembic runs sync; we convert the async aiosqlite URL to sync sqlite)
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_DB_PATH = str(_BACKEND_DIR / "treff.db")
SYNC_DATABASE_URL = f"sqlite:///{_DB_PATH}"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    emitting SQL to stdout instead of executing it.
    """
    context.configure(
        url=SYNC_DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # Required for SQLite ALTER TABLE support
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates a synchronous Engine and runs migrations against it.
    Uses batch mode for SQLite compatibility (ALTER TABLE limitations).
    """
    connectable = create_engine(
        SYNC_DATABASE_URL,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # Required for SQLite ALTER TABLE support
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

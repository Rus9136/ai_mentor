"""
Alembic environment configuration for SQLAlchemy.
Uses synchronous driver (psycopg2) for migrations.
"""
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Import Base and all models
from app.core.database import Base
import app.models  # noqa: F401 - This import is needed for Alembic to detect models

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Build database URL from environment variables for migrations
# This avoids issues with special characters (@, !, etc.) in passwords
# Priority: environment vars > alembic.ini
def get_migration_url() -> str | None:
    """Build migration database URL from environment variables."""
    # Check if individual components are set
    host = os.environ.get("POSTGRES_HOST")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ.get("POSTGRES_DB")
    password = os.environ.get("POSTGRES_PASSWORD")

    if host and db and password:
        # Use ai_mentor_user (SUPERUSER) for migrations, not POSTGRES_USER (ai_mentor_app)
        user = "ai_mentor_user"
        # URL-encode special characters in password
        from urllib.parse import quote_plus
        encoded_password = quote_plus(password)
        return f"postgresql://{user}:{encoded_password}@{host}:{port}/{db}"
    return None

# Store URL globally for use in run_migrations_online()
MIGRATION_URL = get_migration_url()

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Use MIGRATION_URL from env vars if available, else fallback to alembic.ini
    url = MIGRATION_URL or config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    from sqlalchemy import create_engine

    # Use MIGRATION_URL from env vars if available, else fallback to alembic.ini
    if MIGRATION_URL:
        connectable = create_engine(MIGRATION_URL, poolclass=pool.NullPool)
    else:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
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

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

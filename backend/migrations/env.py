"""Alembic environment.

The database URL comes from ``app.database`` (the ``DATABASE_URL`` env var), so
migrations and the running app always talk to the same database.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context

from app import models  # noqa: F401  (registers every table on Base.metadata)
from app.database import Base, engine

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _configure(**kwargs) -> None:
    context.configure(
        target_metadata=target_metadata,
        # SQLite can't ALTER most things in place; batch mode copies the table.
        render_as_batch=True,
        compare_type=True,
        **kwargs,
    )


def run_migrations_offline() -> None:
    """Print the SQL instead of running it (``alembic upgrade head --sql``)."""
    _configure(url=engine.url, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Tests hand in their own connection (to a throwaway database).
    connection = config.attributes.get("connection")
    if connection is not None:
        _configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()
        return

    with engine.connect() as connection:
        _configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

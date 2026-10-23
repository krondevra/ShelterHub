"""The Alembic migrations build the same schema as the models."""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect

from app.database import Base

BACKEND_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture()
def migration_engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'migrations.db'}")
    yield engine
    engine.dispose()


def run(engine, action, revision):
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        action(config, revision)


def test_upgrade_creates_every_table(migration_engine):
    run(migration_engine, command.upgrade, "head")

    tables = set(inspect(migration_engine).get_table_names())
    assert set(Base.metadata.tables) <= tables


def test_migrations_match_the_models(migration_engine):
    """Same check as `alembic check`: nothing left for autogenerate to add."""
    run(migration_engine, command.upgrade, "head")

    with migration_engine.connect() as connection:
        context = MigrationContext.configure(connection, opts={"compare_type": True})
        assert compare_metadata(context, Base.metadata) == []


def test_status_columns_reject_unknown_values(migration_engine):
    run(migration_engine, command.upgrade, "head")

    with migration_engine.begin() as connection:
        connection.exec_driver_sql("INSERT INTO shelters (id, name, created_at) VALUES (1, 'S', '2026-01-01')")
        with pytest.raises(Exception, match="CHECK"):
            connection.exec_driver_sql(
                "INSERT INTO animals (name, species, breed, age, status, shelter_id, created_at) "
                "VALUES ('Rex', 'dog', 'lab', 1, 'sold', 1, '2026-01-01')"
            )


def test_downgrade_removes_everything(migration_engine):
    run(migration_engine, command.upgrade, "head")
    run(migration_engine, command.downgrade, "base")

    assert set(inspect(migration_engine).get_table_names()) <= {"alembic_version"}

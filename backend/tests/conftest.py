"""Shared pytest fixtures.

Every test runs against a throwaway in-memory SQLite database -- the real
PostgreSQL instance is never touched. The environment defaults that make that
true are set in ``tests/__init__.py``, which is imported before this module.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Shelter


@pytest.fixture()
def engine():
    """A fresh in-memory database per test.

    ``StaticPool`` keeps every session on the one connection, which is what
    makes ``:memory:`` visible to both the fixtures and the request handlers.
    """
    test_engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


@pytest.fixture()
def session_factory(engine):
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture()
def db(session_factory) -> Session:
    """Direct database access, for the model-layer tests."""
    with session_factory() as session:
        yield session


@pytest.fixture()
def client(session_factory):
    """HTTP client wired to the test database.

    ``TestClient`` is deliberately *not* used as a context manager: that would
    run the app lifespan, which creates tables and seeds demo data on the
    application's own engine rather than this test's.
    """

    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def shelter_id(db) -> int:
    """A persisted shelter, since animals cannot exist without one."""
    shelter = Shelter(name="Test Shelter", city="Riga")
    db.add(shelter)
    db.commit()
    return shelter.id


# ------------------------------------------------------------------ helpers ---
def register(client: TestClient, email: str, role: str, password: str = "password123"):
    return client.post(
        "/auth/register", json={"email": email, "password": password, "role": role}
    )


def login_headers(
    client: TestClient, email: str, password: str = "password123"
) -> dict[str, str]:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def account(client: TestClient, email: str, role: str) -> dict[str, str]:
    """Register a user and return ready-to-use auth headers."""
    response = register(client, email, role)
    assert response.status_code == 201, response.text
    return login_headers(client, email)


@pytest.fixture()
def staff_headers(client) -> dict[str, str]:
    return account(client, "staff@example.com", "staff")


@pytest.fixture()
def adopter_headers(client) -> dict[str, str]:
    return account(client, "adopter@example.com", "adopter")


@pytest.fixture()
def animal_id(client, staff_headers, shelter_id) -> int:
    """A persisted, available animal."""
    response = client.post(
        "/animals",
        json={
            "name": "Rex",
            "species": "dog",
            "breed": "labrador",
            "age": 3,
            "shelter_id": shelter_id,
        },
        headers=staff_headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]

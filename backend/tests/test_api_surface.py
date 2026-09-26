"""Shelter listing, health check, and conformance with docs/API_CONTRACT.md."""

from __future__ import annotations

from app.models import Shelter
from app.seed import DEMO_SHELTERS, seed_shelters

#: Every route the contract defines, plus the two documented additions
#: (``GET /shelters`` and the pre-existing ``/health``).
EXPECTED_ROUTES = {
    "/auth/register": {"post"},
    "/auth/login": {"post"},
    "/animals": {"get", "post"},
    "/animals/{animal_id}": {"get", "patch"},
    "/applications": {"post", "get"},
    "/applications/{application_id}": {"patch"},
    "/shelters": {"get"},
    "/health": {"get"},
}


def test_the_api_exposes_exactly_the_contracted_routes(client):
    paths = client.get("/openapi.json").json()["paths"]

    assert {path: set(methods) for path, methods in paths.items()} == EXPECTED_ROUTES


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_errors_use_the_contract_error_format(client):
    response = client.get("/animals/999")

    assert response.status_code == 404
    assert set(response.json()) == {"detail"}
    assert isinstance(response.json()["detail"], str)


# ---------------------------------------------------------------- shelters ---
def test_shelter_listing_is_public_and_starts_empty(client):
    response = client.get("/shelters")

    assert response.status_code == 200
    assert response.json() == []


def test_shelter_listing_returns_the_documented_shape(client, shelter_id):
    response = client.get("/shelters")

    assert response.status_code == 200
    assert response.json() == [
        {"id": shelter_id, "name": "Test Shelter", "city": "Riga"}
    ]


# -------------------------------------------------------------------- seed ---
def test_seeding_populates_an_empty_database(db):
    added = seed_shelters(db)

    assert added == len(DEMO_SHELTERS)
    assert db.query(Shelter).count() == len(DEMO_SHELTERS)


def test_seeding_is_idempotent(db):
    seed_shelters(db)
    added_again = seed_shelters(db)

    assert added_again == 0
    assert db.query(Shelter).count() == len(DEMO_SHELTERS)

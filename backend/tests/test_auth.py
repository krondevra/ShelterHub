"""Auth route tests: registration, login, and role-based access control."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models import Adopter, Staff, User

from .conftest import account, register


# ---------------------------------------------------------------- register ---
@pytest.mark.parametrize("role", ["adopter", "staff"])
def test_register_returns_the_contract_shape(client, role):
    response = register(client, f"{role}@example.com", role)

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"id", "email", "role"}
    assert body["email"] == f"{role}@example.com"
    assert body["role"] == role
    assert isinstance(body["id"], int)


def test_register_instantiates_the_subclass_named_by_role(client, db):
    register(client, "s@example.com", "staff")
    register(client, "a@example.com", "adopter")

    users = {u.email: u for u in db.scalars(select(User)).all()}
    assert isinstance(users["s@example.com"], Staff)
    assert isinstance(users["a@example.com"], Adopter)


def test_register_never_stores_the_plaintext_password(client, db):
    register(client, "a@example.com", "adopter", password="password123")

    user = db.scalar(select(User).where(User.email == "a@example.com"))
    assert user.hashed_password != "password123"
    assert user.hashed_password.startswith("$2")  # bcrypt


def test_duplicate_email_is_rejected(client):
    register(client, "a@example.com", "adopter")
    response = register(client, "a@example.com", "staff")

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"


def test_email_is_normalised_to_lowercase(client):
    assert (
        register(client, "Mixed@EXAMPLE.com", "adopter").json()["email"]
        == "mixed@example.com"
    )
    assert register(client, "mixed@example.com", "adopter").status_code == 409


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "not-an-email", "password": "password123", "role": "adopter"},
        {"email": "a@example.com", "password": "short", "role": "adopter"},
        {"email": "a@example.com", "password": "password123", "role": "administrator"},
        {"email": "a@example.com", "password": "password123"},
    ],
    ids=["bad-email", "short-password", "unknown-role", "missing-role"],
)
def test_invalid_registration_payloads_are_rejected(client, payload):
    assert client.post("/auth/register", json=payload).status_code == 422


# ------------------------------------------------------------------- login ---
def test_login_returns_a_bearer_token(client):
    register(client, "a@example.com", "adopter")
    response = client.post(
        "/auth/login", json={"email": "a@example.com", "password": "password123"}
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"access_token", "token_type"}
    assert body["token_type"] == "bearer"
    assert body["access_token"]


@pytest.mark.parametrize(
    "email,password",
    [("a@example.com", "wrong-password"), ("nobody@example.com", "password123")],
    ids=["wrong-password", "unknown-email"],
)
def test_bad_credentials_are_rejected_identically(client, email, password):
    register(client, "a@example.com", "adopter")
    response = client.post("/auth/login", json={"email": email, "password": password})

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


# ---------------------------------------------------- role-based protection ---
def test_protected_route_requires_a_token(client):
    assert client.get("/applications").status_code == 401


@pytest.mark.parametrize(
    "token", ["not-a-jwt", "a.b.c", ""], ids=["garbage", "fake-jwt", "empty"]
)
def test_invalid_tokens_are_rejected(client, token):
    response = client.get("/applications", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_adopter_cannot_reach_a_staff_only_route(client, adopter_headers, shelter_id):
    response = client.post(
        "/animals",
        json={
            "name": "Rex",
            "species": "dog",
            "breed": "lab",
            "age": 1,
            "shelter_id": shelter_id,
        },
        headers=adopter_headers,
    )

    assert response.status_code == 403
    assert "staff" in response.json()["detail"]


def test_staff_cannot_reach_an_adopter_only_route(client, staff_headers, animal_id):
    response = client.post(
        "/applications", json={"animal_id": animal_id}, headers=staff_headers
    )

    assert response.status_code == 403
    assert "adopter" in response.json()["detail"]


def test_a_token_for_a_deleted_user_is_rejected(client, db):
    headers = account(client, "ghost@example.com", "adopter")
    db.delete(db.scalar(select(User).where(User.email == "ghost@example.com")))
    db.commit()

    assert client.get("/applications", headers=headers).status_code == 401

"""Animal route tests: contract shape, staff-only writes, partial updates."""

from __future__ import annotations

import pytest

from app.models import Shelter

CONTRACT_FIELDS = {"id", "name", "species", "breed", "age", "status", "shelter_id", "photo_url"}


def new_animal_payload(shelter_id: int, **overrides) -> dict:
    payload = {
        "name": "Rex",
        "species": "dog",
        "breed": "labrador",
        "age": 3,
        "shelter_id": shelter_id,
    }
    payload.update(overrides)
    return payload


# -------------------------------------------------------------------- read ---
def test_listing_is_public_and_starts_empty(client):
    response = client.get("/animals")
    assert response.status_code == 200
    assert response.json() == []


def test_listing_returns_only_the_contract_fields(client, animal_id):
    response = client.get("/animals")

    assert response.status_code == 200
    (animal,) = response.json()
    assert set(animal) == CONTRACT_FIELDS


def test_get_single_animal(client, animal_id, shelter_id):
    response = client.get(f"/animals/{animal_id}")

    assert response.status_code == 200
    assert response.json() == {
        "id": animal_id,
        "name": "Rex",
        "species": "dog",
        "breed": "labrador",
        "age": 3,
        "status": "available",
        "shelter_id": shelter_id,
        "photo_url": None,
    }


def test_get_unknown_animal_is_404(client):
    response = client.get("/animals/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Animal 999 not found"


# ------------------------------------------------------------------ create ---
def test_staff_can_create_an_animal_defaulting_to_available(
    client, staff_headers, shelter_id
):
    response = client.post(
        "/animals", json=new_animal_payload(shelter_id), headers=staff_headers
    )

    assert response.status_code == 201
    body = response.json()
    assert set(body) == CONTRACT_FIELDS
    assert body["status"] == "available"
    assert body["shelter_id"] == shelter_id


def test_creating_requires_authentication(client, shelter_id):
    response = client.post("/animals", json=new_animal_payload(shelter_id))
    assert response.status_code == 401


def test_creating_against_an_unknown_shelter_is_404(client, staff_headers):
    response = client.post(
        "/animals", json=new_animal_payload(999), headers=staff_headers
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Shelter 999 not found"


@pytest.mark.parametrize(
    "overrides",
    [{"age": -1}, {"age": 2**31}, {"name": ""}, {"age": "three"}, {"species": None}],
    ids=[
        "negative-age",
        "oversized-age",
        "blank-name",
        "non-numeric-age",
        "null-species",
    ],
)
def test_invalid_create_payloads_are_rejected(
    client, staff_headers, shelter_id, overrides
):
    response = client.post(
        "/animals",
        json=new_animal_payload(shelter_id, **overrides),
        headers=staff_headers,
    )
    assert response.status_code == 422


def test_status_cannot_be_forced_at_creation(client, staff_headers, shelter_id):
    """`status` is not part of the POST contract, so sending it is a 422 --
    the same as for PATCH -- rather than being silently ignored."""
    response = client.post(
        "/animals",
        json=new_animal_payload(shelter_id) | {"status": "adopted"},
        headers=staff_headers,
    )

    assert response.status_code == 422
    assert client.get("/animals").json() == []


# ------------------------------------------------------------------ update ---
def test_staff_can_patch_a_subset_of_fields(client, staff_headers, animal_id):
    response = client.patch(
        f"/animals/{animal_id}",
        json={"age": 5, "breed": "poodle"},
        headers=staff_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert (body["age"], body["breed"]) == (5, "poodle")
    assert body["name"] == "Rex"  # untouched


def test_every_contracted_field_can_be_patched(client, db, staff_headers, animal_id):
    other_shelter = Shelter(name="Other Shelter", city="Tallinn")
    db.add(other_shelter)
    db.commit()
    payload = {
        "name": "Max",
        "species": "cat",
        "breed": "siamese",
        "age": 7,
        "shelter_id": other_shelter.id,
    }

    response = client.patch(
        f"/animals/{animal_id}", json=payload, headers=staff_headers
    )

    assert response.status_code == 200
    assert response.json() == payload | {"id": animal_id, "status": "available", "photo_url": None}


@pytest.mark.parametrize("status", ["available", "pending", "adopted", "sold"])
def test_status_cannot_be_patched(client, staff_headers, animal_id, status):
    """`status` is driven only by the application flow, so even a valid value
    is refused."""
    response = client.patch(
        f"/animals/{animal_id}", json={"status": status}, headers=staff_headers
    )

    assert response.status_code == 422
    assert client.get(f"/animals/{animal_id}").json()["status"] == "available"


def test_a_patch_containing_status_changes_nothing(client, staff_headers, animal_id):
    before = client.get(f"/animals/{animal_id}").json()
    response = client.patch(
        f"/animals/{animal_id}",
        json={"age": 9, "status": "adopted"},
        headers=staff_headers,
    )

    assert response.status_code == 422
    assert client.get(f"/animals/{animal_id}").json() == before


@pytest.mark.parametrize("field", ["name", "species", "breed", "age", "shelter_id"])
def test_a_field_cannot_be_patched_to_null(client, staff_headers, animal_id, field):
    """A field is either sent with a value or left out; `null` is an invalid body."""
    before = client.get(f"/animals/{animal_id}").json()
    response = client.patch(
        f"/animals/{animal_id}", json={field: None}, headers=staff_headers
    )

    assert response.status_code == 422
    assert client.get(f"/animals/{animal_id}").json() == before


def test_empty_patch_leaves_the_animal_unchanged(client, staff_headers, animal_id):
    before = client.get(f"/animals/{animal_id}").json()
    response = client.patch(f"/animals/{animal_id}", json={}, headers=staff_headers)

    assert response.status_code == 200
    assert response.json() == before


def test_adopter_cannot_patch(client, adopter_headers, animal_id):
    response = client.patch(
        f"/animals/{animal_id}", json={"age": 9}, headers=adopter_headers
    )
    assert response.status_code == 403


def test_patching_an_unknown_animal_is_404(client, staff_headers):
    response = client.patch("/animals/999", json={"age": 9}, headers=staff_headers)
    assert response.status_code == 404


def test_patching_to_an_unknown_shelter_is_404(client, staff_headers, animal_id):
    response = client.patch(
        f"/animals/{animal_id}", json={"shelter_id": 999}, headers=staff_headers
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Shelter 999 not found"


@pytest.mark.parametrize(
    "payload",
    [{"age": -2}, {"age": 2**31}, {"unknown_field": 1}],
    ids=["negative-age", "oversized-age", "unknown-field"],
)
def test_invalid_patch_payloads_are_rejected(client, staff_headers, animal_id, payload):
    response = client.patch(
        f"/animals/{animal_id}", json=payload, headers=staff_headers
    )
    assert response.status_code == 422

"""Animal route tests: contract shape, staff-only writes, partial updates."""

from __future__ import annotations

import pytest

CONTRACT_FIELDS = {"id", "name", "species", "breed", "age", "status", "shelter_id"}


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
    [{"age": -1}, {"name": ""}, {"age": "three"}, {"species": None}],
    ids=["negative-age", "blank-name", "non-numeric-age", "null-species"],
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
    """`status` is not part of the POST contract, so it must be ignored."""
    response = client.post(
        "/animals",
        json=new_animal_payload(shelter_id) | {"status": "adopted"},
        headers=staff_headers,
    )

    assert response.status_code == 201
    assert response.json()["status"] == "available"


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


def test_staff_can_patch_the_status_directly(client, staff_headers, animal_id):
    response = client.patch(
        f"/animals/{animal_id}", json={"status": "adopted"}, headers=staff_headers
    )

    assert response.status_code == 200
    assert response.json()["status"] == "adopted"


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
    [{"status": "sold"}, {"age": -2}, {"unknown_field": 1}],
    ids=["bad-status", "negative-age", "unknown-field"],
)
def test_invalid_patch_payloads_are_rejected(client, staff_headers, animal_id, payload):
    response = client.patch(
        f"/animals/{animal_id}", json=payload, headers=staff_headers
    )
    assert response.status_code == 422

"""Application route tests, covering the available -> pending -> adopted flow."""

from __future__ import annotations

from datetime import datetime

import pytest

from .conftest import account

CONTRACT_FIELDS = {"id", "adopter_id", "animal_id", "status", "created_at"}


def apply_for(client, animal_id: int, headers: dict[str, str]):
    return client.post("/applications", json={"animal_id": animal_id}, headers=headers)


def animal_status(client, animal_id: int) -> str:
    return client.get(f"/animals/{animal_id}").json()["status"]


@pytest.fixture()
def other_adopter_headers(client) -> dict[str, str]:
    return account(client, "second@example.com", "adopter")


# ------------------------------------------------------------------ create ---
def test_applying_returns_the_contract_shape(client, adopter_headers, animal_id):
    response = apply_for(client, animal_id, adopter_headers)

    assert response.status_code == 201
    body = response.json()
    assert set(body) == CONTRACT_FIELDS
    assert body["status"] == "pending"
    assert body["animal_id"] == animal_id
    assert datetime.fromisoformat(body["created_at"])


def test_applying_moves_the_animal_to_pending(client, adopter_headers, animal_id):
    assert animal_status(client, animal_id) == "available"

    apply_for(client, animal_id, adopter_headers)

    assert animal_status(client, animal_id) == "pending"


def test_application_is_attributed_to_the_caller(client, adopter_headers, animal_id):
    me = client.get("/applications", headers=adopter_headers)
    body = apply_for(client, animal_id, adopter_headers).json()

    assert me.json() == []
    assert body["adopter_id"] > 0


def test_applying_requires_authentication(client, animal_id):
    assert (
        client.post("/applications", json={"animal_id": animal_id}).status_code == 401
    )


def test_applying_for_an_unknown_animal_is_404(client, adopter_headers):
    response = apply_for(client, 999, adopter_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Animal 999 not found"


def test_the_same_adopter_cannot_apply_twice(client, adopter_headers, animal_id):
    apply_for(client, animal_id, adopter_headers)
    response = apply_for(client, animal_id, adopter_headers)

    assert response.status_code == 409
    assert "already have a pending application" in response.json()["detail"]


def test_a_second_adopter_may_compete_for_a_pending_animal(
    client, adopter_headers, other_adopter_headers, animal_id
):
    apply_for(client, animal_id, adopter_headers)
    response = apply_for(client, animal_id, other_adopter_headers)

    assert response.status_code == 201
    assert animal_status(client, animal_id) == "pending"


def test_nobody_can_apply_for_an_adopted_animal(
    client, staff_headers, other_adopter_headers, animal_id
):
    client.patch(
        f"/animals/{animal_id}", json={"status": "adopted"}, headers=staff_headers
    )
    response = apply_for(client, animal_id, other_adopter_headers)

    assert response.status_code == 409
    assert response.json()["detail"] == f"Animal {animal_id} has already been adopted"


# -------------------------------------------------------------------- list ---
def test_adopters_see_only_their_own_applications(
    client, adopter_headers, other_adopter_headers, animal_id
):
    mine = apply_for(client, animal_id, adopter_headers).json()
    apply_for(client, animal_id, other_adopter_headers)

    response = client.get("/applications", headers=adopter_headers)

    assert response.status_code == 200
    assert [app["id"] for app in response.json()] == [mine["id"]]


def test_staff_see_every_application(
    client, staff_headers, adopter_headers, other_adopter_headers, animal_id
):
    apply_for(client, animal_id, adopter_headers)
    apply_for(client, animal_id, other_adopter_headers)

    response = client.get("/applications", headers=staff_headers)

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_listing_requires_authentication(client):
    assert client.get("/applications").status_code == 401


# ---------------------------------------------------------------- decisions ---
def test_approving_adopts_the_animal(client, staff_headers, adopter_headers, animal_id):
    application = apply_for(client, animal_id, adopter_headers).json()

    response = client.patch(
        f"/applications/{application['id']}",
        json={"status": "approved"},
        headers=staff_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert animal_status(client, animal_id) == "adopted"


def test_approving_rejects_the_competing_applications(
    client, staff_headers, adopter_headers, other_adopter_headers, animal_id
):
    winner = apply_for(client, animal_id, adopter_headers).json()
    loser = apply_for(client, animal_id, other_adopter_headers).json()

    client.patch(
        f"/applications/{winner['id']}",
        json={"status": "approved"},
        headers=staff_headers,
    )

    everything = {
        app["id"]: app["status"]
        for app in client.get("/applications", headers=staff_headers).json()
    }
    assert everything == {winner["id"]: "approved", loser["id"]: "rejected"}
    assert animal_status(client, animal_id) == "adopted"


def test_rejecting_the_last_application_frees_the_animal(
    client, staff_headers, adopter_headers, animal_id
):
    application = apply_for(client, animal_id, adopter_headers).json()

    response = client.patch(
        f"/applications/{application['id']}",
        json={"status": "rejected"},
        headers=staff_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert animal_status(client, animal_id) == "available"


def test_rejecting_one_of_two_leaves_the_animal_pending(
    client, staff_headers, adopter_headers, other_adopter_headers, animal_id
):
    first = apply_for(client, animal_id, adopter_headers).json()
    apply_for(client, animal_id, other_adopter_headers)

    client.patch(
        f"/applications/{first['id']}",
        json={"status": "rejected"},
        headers=staff_headers,
    )

    assert animal_status(client, animal_id) == "pending"


def test_rejecting_never_un_adopts_an_animal(
    client, staff_headers, adopter_headers, animal_id
):
    application = apply_for(client, animal_id, adopter_headers).json()
    client.patch(
        f"/animals/{animal_id}", json={"status": "adopted"}, headers=staff_headers
    )

    client.patch(
        f"/applications/{application['id']}",
        json={"status": "rejected"},
        headers=staff_headers,
    )

    assert animal_status(client, animal_id) == "adopted"


def test_an_application_can_only_be_decided_once(
    client, staff_headers, adopter_headers, animal_id
):
    application = apply_for(client, animal_id, adopter_headers).json()
    client.patch(
        f"/applications/{application['id']}",
        json={"status": "approved"},
        headers=staff_headers,
    )

    response = client.patch(
        f"/applications/{application['id']}",
        json={"status": "rejected"},
        headers=staff_headers,
    )

    assert response.status_code == 409
    assert "already been approved" in response.json()["detail"]


def test_adopters_cannot_decide_applications(client, adopter_headers, animal_id):
    application = apply_for(client, animal_id, adopter_headers).json()

    response = client.patch(
        f"/applications/{application['id']}",
        json={"status": "approved"},
        headers=adopter_headers,
    )
    assert response.status_code == 403


def test_deciding_an_unknown_application_is_404(client, staff_headers):
    response = client.patch(
        "/applications/999", json={"status": "approved"}, headers=staff_headers
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Application 999 not found"


@pytest.mark.parametrize(
    "payload",
    [{"status": "pending"}, {"status": "maybe"}, {}, {"statuses": "approved"}],
    ids=["back-to-pending", "unknown-status", "empty", "unknown-field"],
)
def test_invalid_decisions_are_rejected(
    client, staff_headers, adopter_headers, animal_id, payload
):
    application = apply_for(client, animal_id, adopter_headers).json()

    response = client.patch(
        f"/applications/{application['id']}", json=payload, headers=staff_headers
    )
    assert response.status_code == 422

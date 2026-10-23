"""``python -m app.seed --demo`` data."""

from __future__ import annotations

from sqlalchemy import func, select

from app.models import Animal, AnimalStatus, ShelterApplication, User
from app.seed import DEMO_ADOPTERS, DEMO_ANIMALS, DEMO_PASSWORD, DEMO_STAFF, seed_demo, seed_shelters
from tests.conftest import login_headers


def count(db, model):
    return db.scalar(select(func.count()).select_from(model))


def test_demo_seed_adds_accounts_animals_and_applications(db):
    seed_shelters(db)

    assert seed_demo(db) is True
    assert count(db, User) == 1 + len(DEMO_ADOPTERS)
    assert count(db, Animal) == len(DEMO_ANIMALS)
    assert count(db, ShelterApplication) == 5


def test_demo_seed_runs_only_once(db):
    seed_shelters(db)
    seed_demo(db)

    assert seed_demo(db) is False
    assert count(db, Animal) == len(DEMO_ANIMALS)


def test_demo_statuses_follow_the_application_rules(db):
    """Adopted <=> an approved application; pending <=> an open one."""
    seed_shelters(db)
    seed_demo(db)

    for animal in db.scalars(select(Animal)):
        statuses = {app.status.value for app in animal.applications}
        if "approved" in statuses:
            assert animal.status is AnimalStatus.ADOPTED
            assert "pending" not in statuses
        elif "pending" in statuses:
            assert animal.status is AnimalStatus.PENDING
        else:
            assert animal.status is AnimalStatus.AVAILABLE


def test_demo_accounts_can_log_in(client, db):
    seed_shelters(db)
    seed_demo(db)

    for email in (DEMO_STAFF, *DEMO_ADOPTERS):
        assert "Authorization" in login_headers(client, email, DEMO_PASSWORD)

    staff = login_headers(client, DEMO_STAFF, DEMO_PASSWORD)
    assert len(client.get("/applications", headers=staff).json()) == 5

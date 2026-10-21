"""Model-layer unit tests: inheritance, relationships, and domain helpers."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import (
    Adopter,
    Animal,
    AnimalStatus,
    ApplicationStatus,
    Shelter,
    ShelterApplication,
    Staff,
    User,
)


@pytest.fixture()
def shelter(db) -> Shelter:
    shelter = Shelter(name="Paws Haven", city="Riga")
    db.add(shelter)
    db.commit()
    return shelter


def make_animal(db, shelter: Shelter, name: str = "Rex", **kwargs) -> Animal:
    animal = Animal(
        name=name,
        species=kwargs.pop("species", "dog"),
        breed=kwargs.pop("breed", "labrador"),
        age=kwargs.pop("age", 3),
        shelter=shelter,
        **kwargs,
    )
    db.add(animal)
    db.commit()
    return animal


# ------------------------------------------------------------- inheritance ---
def test_staff_and_adopter_share_the_users_table(db):
    db.add_all(
        [
            Staff(email="s@example.com", hashed_password="h"),
            Adopter(email="a@example.com", hashed_password="h"),
        ]
    )
    db.commit()

    rows = db.scalars(select(User).order_by(User.email)).all()
    assert [type(row).__name__ for row in rows] == ["Adopter", "Staff"]
    assert {row.__tablename__ for row in rows} == {"users"}


def test_role_column_is_populated_from_the_subclass(db):
    staff = Staff(email="s@example.com", hashed_password="h")
    adopter = Adopter(email="a@example.com", hashed_password="h")
    db.add_all([staff, adopter])
    db.commit()

    assert (staff.role, staff.is_staff, staff.is_adopter) == ("staff", True, False)
    assert (adopter.role, adopter.is_adopter, adopter.is_staff) == (
        "adopter",
        True,
        False,
    )


def test_subclass_query_is_filtered_by_discriminator(db):
    db.add_all(
        [
            Staff(email="s@example.com", hashed_password="h"),
            Adopter(email="a1@example.com", hashed_password="h"),
            Adopter(email="a2@example.com", hashed_password="h"),
        ]
    )
    db.commit()

    assert len(db.scalars(select(Adopter)).all()) == 2
    assert len(db.scalars(select(Staff)).all()) == 1
    assert len(db.scalars(select(User)).all()) == 3


def test_email_must_be_unique(db):
    db.add(Adopter(email="dup@example.com", hashed_password="h"))
    db.commit()
    db.add(Staff(email="dup@example.com", hashed_password="h"))

    with pytest.raises(IntegrityError):
        db.commit()


# ------------------------------------------------------------ relationships ---
def test_shelter_has_many_animals(db, shelter):
    make_animal(db, shelter, "Rex")
    make_animal(db, shelter, "Milo")

    db.refresh(shelter)
    assert {a.name for a in shelter.animals} == {"Rex", "Milo"}
    assert all(a.shelter is shelter for a in shelter.animals)


def test_shelter_employs_staff(db, shelter):
    member = Staff(email="s@example.com", hashed_password="h", shelter=shelter)
    db.add(member)
    db.commit()

    db.refresh(shelter)
    assert shelter.staff == [member]
    assert member.shelter_id == shelter.id


def test_adopter_and_animal_both_own_applications(db, shelter):
    animal = make_animal(db, shelter)
    adopter = Adopter(email="a@example.com", hashed_password="h")
    db.add(adopter)
    db.commit()

    application = ShelterApplication(adopter=adopter, animal=animal)
    db.add(application)
    db.commit()

    assert adopter.applications == [application]
    assert animal.applications == [application]
    assert application.adopter is adopter
    assert application.animal is animal


def test_deleting_an_animal_cascades_to_its_applications(db, shelter):
    animal = make_animal(db, shelter)
    adopter = Adopter(email="a@example.com", hashed_password="h")
    db.add(adopter)
    db.commit()
    db.add(ShelterApplication(adopter=adopter, animal=animal))
    db.commit()

    db.delete(animal)
    db.commit()

    assert db.scalars(select(ShelterApplication)).all() == []


# ------------------------------------------------------------------ domain ---
def test_animal_defaults_to_available(db, shelter):
    animal = make_animal(db, shelter)
    assert animal.status is AnimalStatus.AVAILABLE
    assert animal.is_available is True


def test_application_defaults_to_pending(db, shelter):
    animal = make_animal(db, shelter)
    adopter = Adopter(email="a@example.com", hashed_password="h")
    db.add(adopter)
    db.commit()
    application = ShelterApplication(adopter=adopter, animal=animal)
    db.add(application)
    db.commit()

    assert application.status is ApplicationStatus.PENDING
    assert application.is_open is True
    assert application.created_at is not None


def test_open_application_helpers(db, shelter):
    animal = make_animal(db, shelter)
    other = make_animal(db, shelter, "Milo")
    adopter = Adopter(email="a@example.com", hashed_password="h")
    db.add(adopter)
    db.commit()

    application = ShelterApplication(adopter=adopter, animal=animal)
    db.add(application)
    db.commit()

    assert adopter.has_open_application_for(animal.id) is True
    assert adopter.has_open_application_for(other.id) is False
    assert animal.open_applications() == [application]

    application.status = ApplicationStatus.REJECTED
    db.commit()

    assert adopter.has_open_application_for(animal.id) is False
    assert animal.open_applications() == []


def test_shelter_available_animals_excludes_adopted(db, shelter):
    available = make_animal(db, shelter, "Rex")
    make_animal(db, shelter, "Milo", status=AnimalStatus.ADOPTED)

    db.refresh(shelter)
    assert shelter.available_animals == [available]


def test_negative_age_is_rejected_by_the_check_constraint(db, shelter):
    db.add(Animal(name="Rex", species="dog", breed="labrador", age=-1, shelter=shelter))
    with pytest.raises(IntegrityError):
        db.commit()

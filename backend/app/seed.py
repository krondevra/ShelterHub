"""Seed data.

The contract defines no endpoint that creates a shelter, yet ``POST /animals``
requires a ``shelter_id``, so the shelters are always seeded. ``--demo`` adds
demo accounts, animals and applications for trying the app out.

Run after the migrations (the Docker entrypoint does both):

    python -m app.seed           # shelters only
    python -m app.seed --demo    # shelters + demo data

Both are safe to run again: existing data is left alone.
"""

from __future__ import annotations

import argparse

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import (
    Adopter,
    Animal,
    AnimalStatus,
    ApplicationStatus,
    Shelter,
    ShelterApplication,
    Staff,
    User,
)
from .security import hash_password

DEMO_SHELTERS: tuple[tuple[str, str], ...] = (
    ("Paws Haven", "Riga"),
    ("Second Chance Shelter", "Vilnius"),
    ("Happy Tails Rescue", "Tallinn"),
)


def seed_shelters(db: Session) -> int:
    """Insert the demo shelters if the table is empty. Returns rows added."""
    if db.scalar(select(func.count()).select_from(Shelter)):
        return 0
    db.add_all([Shelter(name=name, city=city) for name, city in DEMO_SHELTERS])
    db.commit()
    return len(DEMO_SHELTERS)


DEMO_PASSWORD = "password123"
DEMO_STAFF = "staff@example.com"
DEMO_ADOPTERS = ("anna@example.com", "janis@example.com")

# (name, species, breed, age, shelter name)
DEMO_ANIMALS: tuple[tuple[str, str, str, int, str], ...] = (
    ("Max", "Dog", "Labrador", 3, "Paws Haven"),
    ("Bella", "Cat", "British Shorthair", 2, "Paws Haven"),
    ("Rocky", "Dog", "German Shepherd", 5, "Paws Haven"),
    ("Luna", "Cat", "Siamese", 1, "Paws Haven"),
    ("Charlie", "Dog", "Beagle", 4, "Second Chance Shelter"),
    ("Milo", "Cat", "Maine Coon", 6, "Second Chance Shelter"),
    ("Daisy", "Dog", "Dachshund", 0, "Second Chance Shelter"),
    ("Oscar", "Rabbit", "Holland Lop", 2, "Happy Tails Rescue"),
    ("Nala", "Cat", "Tabby", 9, "Happy Tails Rescue"),
    ("Buddy", "Dog", "Golden Retriever", 11, "Happy Tails Rescue"),
)


def seed_demo(db: Session) -> bool:
    """Add demo accounts, animals and applications. Returns False (and changes
    nothing) if the demo staff account already exists.

    The applications follow the contract's status rules, so the data looks
    like it went through the API: Max was adopted by Anna (Janis's competing
    application rejected), both adopters are waiting on Bella, and Janis was
    turned down for Luna, who is available again.
    """
    if db.scalar(select(User).where(User.email == DEMO_STAFF)):
        return False

    password = hash_password(DEMO_PASSWORD)
    db.add(Staff(email=DEMO_STAFF, hashed_password=password))
    anna, janis = (Adopter(email=email, hashed_password=password) for email in DEMO_ADOPTERS)
    db.add_all([anna, janis])

    shelters = {s.name: s for s in db.scalars(select(Shelter))}
    animals = {
        name: Animal(name=name, species=species, breed=breed, age=age, shelter=shelters[shelter])
        for name, species, breed, age, shelter in DEMO_ANIMALS
    }
    db.add_all(animals.values())

    animals["Max"].status = AnimalStatus.ADOPTED
    animals["Bella"].status = AnimalStatus.PENDING
    db.add_all(
        [
            ShelterApplication(adopter=anna, animal=animals["Max"], status=ApplicationStatus.APPROVED),
            ShelterApplication(adopter=janis, animal=animals["Max"], status=ApplicationStatus.REJECTED),
            ShelterApplication(adopter=anna, animal=animals["Bella"], status=ApplicationStatus.PENDING),
            ShelterApplication(adopter=janis, animal=animals["Bella"], status=ApplicationStatus.PENDING),
            ShelterApplication(adopter=janis, animal=animals["Luna"], status=ApplicationStatus.REJECTED),
        ]
    )
    db.commit()
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the ShelterHub database.")
    parser.add_argument("--demo", action="store_true", help="also add demo accounts, animals and applications")
    args = parser.parse_args()

    with SessionLocal() as db:
        print(f"shelters: {seed_shelters(db)} added")
        if args.demo:
            added = seed_demo(db)
            print("demo data: added" if added else "demo data: already there")


if __name__ == "__main__":
    main()

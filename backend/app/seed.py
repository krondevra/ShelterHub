"""Demo data.

The contract defines no endpoint that creates a shelter, yet ``POST /animals``
requires a ``shelter_id``. Seeding a few shelters on startup keeps the contract
untouched while leaving the API usable out of the box.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Shelter

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

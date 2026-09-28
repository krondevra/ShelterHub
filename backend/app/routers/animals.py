"""Animal routes -- ``GET/POST /animals`` and ``GET/PATCH /animals/{id}``."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Animal, Shelter, Staff
from ..schemas import AnimalCreate, AnimalOut, AnimalUpdate
from ..security import require_staff

router = APIRouter(prefix="/animals", tags=["animals"])


def _get_animal_or_404(db: Session, animal_id: int) -> Animal:
    animal = db.get(Animal, animal_id)
    if animal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal {animal_id} not found",
        )
    return animal


def _assert_shelter_exists(db: Session, shelter_id: int) -> None:
    if db.get(Shelter, shelter_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shelter {shelter_id} not found",
        )


@router.get("", response_model=list[AnimalOut])
def list_animals(db: Session = Depends(get_db)) -> list[Animal]:
    """Public catalogue of every registered animal."""
    return list(db.scalars(select(Animal).order_by(Animal.id)).all())


@router.get("/{animal_id}", response_model=AnimalOut)
def get_animal(animal_id: int, db: Session = Depends(get_db)) -> Animal:
    """Fetch a single animal."""
    return _get_animal_or_404(db, animal_id)


@router.post("", response_model=AnimalOut, status_code=status.HTTP_201_CREATED)
def create_animal(
    payload: AnimalCreate,
    db: Session = Depends(get_db),
    _staff: Staff = Depends(require_staff),
) -> Animal:
    """Register a new animal. Status always starts at ``available``."""
    _assert_shelter_exists(db, payload.shelter_id)

    animal = Animal(**payload.model_dump())
    db.add(animal)
    db.commit()
    db.refresh(animal)
    return animal


@router.patch("/{animal_id}", response_model=AnimalOut)
def update_animal(
    animal_id: int,
    payload: AnimalUpdate,
    db: Session = Depends(get_db),
    _staff: Staff = Depends(require_staff),
) -> Animal:
    """Apply a partial update. Omitted fields are left untouched."""
    animal = _get_animal_or_404(db, animal_id)
    updates = payload.model_dump(exclude_unset=True)

    if "shelter_id" in updates:
        _assert_shelter_exists(db, updates["shelter_id"])

    for field, value in updates.items():
        setattr(animal, field, value)

    db.commit()
    db.refresh(animal)
    return animal

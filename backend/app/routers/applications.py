"""Adoption application routes.

Implements the status flow ``available -> pending -> adopted`` described in
docs/UML_MODELS.md. The transitions that the original contract leaves
unspecified are listed in docs/BACKEND_DECISIONS.md.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    Adopter,
    Animal,
    AnimalStatus,
    ApplicationStatus,
    ShelterApplication,
    Staff,
    User,
)
from ..schemas import ApplicationCreate, ApplicationOut, ApplicationUpdate
from ..security import get_current_user, require_adopter, require_staff

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
    adopter: Adopter = Depends(require_adopter),
) -> ShelterApplication:
    """Apply to adopt an animal, moving that animal to ``pending``."""
    animal = db.get(Animal, payload.animal_id)
    if animal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal {payload.animal_id} not found",
        )

    # Checked first so a repeat applicant gets the precise reason rather than a
    # generic conflict caused by their own earlier application.
    if adopter.has_open_application_for(animal.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"You already have a pending application for animal {animal.id}",
        )

    # Only an adopted animal is off the table. Several adopters may compete for
    # the same `pending` animal -- staff then pick one, which rejects the rest.
    if animal.status is AnimalStatus.ADOPTED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Animal {animal.id} has already been adopted",
        )

    application = ShelterApplication(
        adopter_id=adopter.id,
        animal_id=animal.id,
        status=ApplicationStatus.PENDING,
    )
    if animal.status is AnimalStatus.AVAILABLE:
        animal.status = AnimalStatus.PENDING
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@router.get("", response_model=list[ApplicationOut])
def list_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ShelterApplication]:
    """Staff see every application; adopters see only their own."""
    stmt = select(ShelterApplication).order_by(ShelterApplication.id)
    if not isinstance(current_user, Staff):
        stmt = stmt.where(ShelterApplication.adopter_id == current_user.id)
    return list(db.scalars(stmt).all())


@router.patch("/{application_id}", response_model=ApplicationOut)
def decide_application(
    application_id: int,
    payload: ApplicationUpdate,
    db: Session = Depends(get_db),
    _staff: Staff = Depends(require_staff),
) -> ShelterApplication:
    """Approve or reject an application and reconcile the animal's status."""
    application = db.get(ShelterApplication, application_id)
    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found",
        )
    if not application.is_open:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Application {application_id} has already been "
                f"{application.status.value}"
            ),
        )

    decision = ApplicationStatus(payload.status)
    application.status = decision
    animal = application.animal
    others = [app for app in animal.applications if app.id != application.id]

    if decision is ApplicationStatus.APPROVED:
        # Contract: approving an application marks the animal adopted.
        animal.status = AnimalStatus.ADOPTED
        # Nobody else can adopt it now, so close the competing applications.
        for other in others:
            if other.is_open:
                other.status = ApplicationStatus.REJECTED
    elif animal.status is AnimalStatus.PENDING and not any(o.is_open for o in others):
        # Last open application withdrawn -- put the animal back on the market.
        animal.status = AnimalStatus.AVAILABLE

    db.commit()
    db.refresh(application)
    return application

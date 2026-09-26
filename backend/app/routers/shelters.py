"""Read-only shelter listing.

Not in the original contract -- added so the frontend can offer a shelter
picker when creating an animal. See docs/BACKEND_DECISIONS.md.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Shelter
from ..schemas import ShelterOut

router = APIRouter(prefix="/shelters", tags=["shelters"])


@router.get("", response_model=list[ShelterOut])
def list_shelters(db: Session = Depends(get_db)) -> list[Shelter]:
    """List every shelter, oldest first."""
    return list(db.scalars(select(Shelter).order_by(Shelter.id)).all())

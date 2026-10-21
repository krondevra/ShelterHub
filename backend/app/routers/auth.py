"""Registration and login -- ``POST /auth/register``, ``POST /auth/login``."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Adopter, Staff, User, UserRole
from ..schemas import LoginRequest, RegisterRequest, TokenOut, UserOut
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

#: Maps the public ``role`` value onto the concrete subclass to instantiate.
_ROLE_MODELS: dict[UserRole, type[User]] = {
    UserRole.STAFF: Staff,
    UserRole.ADOPTER: Adopter,
}


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> User:
    """Create a new account, instantiating the subclass the role names."""
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    user = _ROLE_MODELS[payload.role](
        email=email, hashed_password=hash_password(payload.password)
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:  # lost a race against a concurrent registration
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        ) from None
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenOut)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenOut:
    """Exchange email + password for a bearer token."""
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    # Same message either way, so the response cannot be used to enumerate emails.
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenOut(access_token=create_access_token(user))

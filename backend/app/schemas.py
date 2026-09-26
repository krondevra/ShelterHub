"""Pydantic request/response models.

Every response model mirrors docs/API_CONTRACT.md field-for-field -- no extra
keys are exposed, which is why `created_at` appears on `ApplicationOut` but not
on `AnimalOut` even though both tables carry the column.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .models import AnimalStatus, ApplicationStatus, UserRole

# bcrypt hashes at most 72 bytes; anything longer is silently ignored, so it is
# rejected up front instead.
Password = Field(min_length=8, max_length=72)


# --------------------------------------------------------------------- auth ---
class RegisterRequest(BaseModel):
    """Body of ``POST /auth/register``."""

    email: EmailStr
    password: str = Password
    role: UserRole


class LoginRequest(BaseModel):
    """Body of ``POST /auth/login``."""

    email: EmailStr
    password: str


class UserOut(BaseModel):
    """``201`` response of ``POST /auth/register``."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    role: UserRole


class TokenOut(BaseModel):
    """``200`` response of ``POST /auth/login``."""

    access_token: str
    token_type: Literal["bearer"] = "bearer"


# ------------------------------------------------------------------ animals ---
class AnimalCreate(BaseModel):
    """Body of ``POST /animals``. ``status`` is not accepted: it defaults to
    ``available`` per the contract."""

    name: str = Field(min_length=1, max_length=120)
    species: str = Field(min_length=1, max_length=80)
    breed: str = Field(min_length=1, max_length=120)
    age: int = Field(ge=0)
    shelter_id: int


class AnimalUpdate(BaseModel):
    """Body of ``PATCH /animals/{id}`` -- any subset of the mutable fields."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=120)
    species: str | None = Field(default=None, min_length=1, max_length=80)
    breed: str | None = Field(default=None, min_length=1, max_length=120)
    age: int | None = Field(default=None, ge=0)
    status: AnimalStatus | None = None
    shelter_id: int | None = None


class AnimalOut(BaseModel):
    """Animal representation used by every animal response in the contract."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    species: str
    breed: str
    age: int
    status: AnimalStatus
    shelter_id: int


# ------------------------------------------------------------- applications ---
class ApplicationCreate(BaseModel):
    """Body of ``POST /applications``."""

    animal_id: int


class ApplicationUpdate(BaseModel):
    """Body of ``PATCH /applications/{id}``.

    Only the two terminal decisions are accepted -- an application cannot be
    moved back to ``pending``.
    """

    model_config = ConfigDict(extra="forbid")

    status: Literal["approved", "rejected"]


class ApplicationOut(BaseModel):
    """Application representation used by every application response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    adopter_id: int
    animal_id: int
    status: ApplicationStatus
    created_at: datetime


# ----------------------------------------------------------------- shelters ---
class ShelterOut(BaseModel):
    """``200`` response of ``GET /shelters``.

    Not part of the original contract -- see docs/BACKEND_DECISIONS.md.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    city: str | None

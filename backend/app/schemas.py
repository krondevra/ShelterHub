"""Pydantic request/response models.

Every response model mirrors docs/API_CONTRACT.md field-for-field -- no extra
keys are exposed, which is why `created_at` appears on `ApplicationOut` but not
on `AnimalOut` even though both tables carry the column.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from .models import AnimalStatus, ApplicationStatus, UserRole

# bcrypt cannot hash more than 72 *bytes*, so anything longer is rejected up
# front. `max_length` counts characters, which is the same thing for ASCII;
# `RegisterRequest` checks the encoded size to cover everything else.
MAX_PASSWORD_BYTES = 72
Password = Field(min_length=8, max_length=MAX_PASSWORD_BYTES)


# --------------------------------------------------------------------- auth ---
class RegisterRequest(BaseModel):
    """Body of ``POST /auth/register``."""

    email: EmailStr
    password: str = Password
    role: UserRole

    @field_validator("password")
    @classmethod
    def _password_fits_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > MAX_PASSWORD_BYTES:
            raise ValueError(
                f"Password must be at most {MAX_PASSWORD_BYTES} bytes long "
                "(non-ASCII characters take more than one)"
            )
        return value


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
# Largest value PostgreSQL's INTEGER column holds. SQLite stores bigger numbers
# without complaint, so only the real database would refuse an oversized age.
MAX_INT32 = 2**31 - 1


class AnimalCreate(BaseModel):
    """Body of ``POST /animals``. ``status`` and ``photo_url`` are not
    accepted: status defaults to ``available`` per the contract, and the photo
    has its own route. ``extra="forbid"`` turns either into a ``422``."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    species: str = Field(min_length=1, max_length=80)
    breed: str = Field(min_length=1, max_length=120)
    age: int = Field(ge=0, le=MAX_INT32)
    shelter_id: int


class AnimalUpdate(BaseModel):
    """Body of ``PATCH /animals/{id}`` -- any subset of the fields below.

    ``status`` is deliberately absent: it is driven only by the application
    flow, and ``extra="forbid"`` turns an attempt to send it into a ``422``.

    Every field is typed non-nullable and merely *defaults* to ``None``, which
    pydantic does not validate. Leaving a field out therefore keeps its current
    value, while an explicit ``null`` is a ``422`` instead of a write to a
    NOT NULL column.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(default=None, min_length=1, max_length=120)
    species: str = Field(default=None, min_length=1, max_length=80)
    breed: str = Field(default=None, min_length=1, max_length=120)
    age: int = Field(default=None, ge=0, le=MAX_INT32)
    shelter_id: int = Field(default=None)


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
    photo_url: str | None


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
    """``200`` response of ``GET /shelters``."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    city: str | None

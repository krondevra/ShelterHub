"""SQLAlchemy domain models for ShelterHub.

The user hierarchy uses **single-table inheritance**: :class:`User` is the
abstract base and :class:`Staff` / :class:`Adopter` are subtypes discriminated
by the ``users.role`` column -- the same ``role`` field the API contract
exposes, so the persistence discriminator and the public API agree by
construction.

Relationships (see docs/UML_MODELS.md):
    Shelter  1 -- *  Animal
    Shelter  1 -- *  Staff
    Adopter  1 -- *  ShelterApplication
    Animal   1 -- *  ShelterApplication
"""

from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _utcnow() -> datetime:
    """Timezone-aware UTC timestamp, applied Python-side.

    Using a Python default rather than ``server_default=func.now()`` keeps the
    value identical on PostgreSQL and on the SQLite test database, and makes it
    readable straight after ``flush()`` without a round trip.
    """
    return datetime.now(timezone.utc)


class UserRole(str, enum.Enum):
    """Values accepted by ``POST /auth/register``."""

    ADOPTER = "adopter"
    STAFF = "staff"


class AnimalStatus(str, enum.Enum):
    """Adoption lifecycle of an animal: available -> pending -> adopted."""

    AVAILABLE = "available"
    PENDING = "pending"
    ADOPTED = "adopted"


class ApplicationStatus(str, enum.Enum):
    """Review lifecycle of an adoption application."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


def _enum_column(py_enum: type[enum.Enum], name: str) -> SAEnum:
    """VARCHAR + CHECK constraint storing enum *values*.

    ``native_enum=False`` avoids a PostgreSQL ENUM type, so the same DDL works
    on SQLite in the test suite.
    """
    return SAEnum(
        py_enum,
        name=name,
        native_enum=False,
        validate_strings=True,
        values_callable=lambda e: [member.value for member in e],
    )


class Shelter(Base):
    """A physical shelter that houses animals and employs staff."""

    __tablename__ = "shelters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    animals: Mapped[list[Animal]] = relationship(
        back_populates="shelter", cascade="all, delete-orphan"
    )
    staff: Mapped[list[Staff]] = relationship(back_populates="shelter")

    @property
    def available_animals(self) -> list[Animal]:
        """Animals at this shelter that can still be applied for."""
        return [a for a in self.animals if a.status is AnimalStatus.AVAILABLE]

    def __repr__(self) -> str:
        return f"<Shelter id={self.id} name={self.name!r}>"


class User(Base):
    """Abstract base of the user hierarchy.

    Never instantiated directly -- it declares no ``polymorphic_identity``, so
    every persisted row is a :class:`Staff` or an :class:`Adopter`.
    """

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('adopter', 'staff')", name="ck_users_role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    # `role` is both the public API field and the inheritance discriminator.
    __mapper_args__ = {"polymorphic_on": role}

    @property
    def is_staff(self) -> bool:
        return self.role == UserRole.STAFF.value

    @property
    def is_adopter(self) -> bool:
        return self.role == UserRole.ADOPTER.value

    def __repr__(self) -> str:
        return f"<{type(self).__name__} id={self.id} email={self.email!r}>"


class Staff(User):
    """Shelter employee: may create and update animals, and review applications."""

    __mapper_args__ = {"polymorphic_identity": UserRole.STAFF.value}

    # Nullable because POST /auth/register does not accept a shelter, and
    # because single-table inheritance shares one table across subtypes.
    shelter_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("shelters.id"), nullable=True
    )
    shelter: Mapped[Shelter | None] = relationship(back_populates="staff")


class Adopter(User):
    """Member of the public who applies to adopt animals."""

    __mapper_args__ = {"polymorphic_identity": UserRole.ADOPTER.value}

    applications: Mapped[list[ShelterApplication]] = relationship(
        back_populates="adopter", cascade="all, delete-orphan"
    )

    def has_open_application_for(self, animal_id: int) -> bool:
        """True if this adopter already awaits a decision on ``animal_id``."""
        return any(
            app.animal_id == animal_id and app.is_open for app in self.applications
        )


class Animal(Base):
    """An animal registered at a shelter and offered for adoption."""

    __tablename__ = "animals"
    __table_args__ = (CheckConstraint("age >= 0", name="ck_animals_age_non_negative"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    species: Mapped[str] = mapped_column(String(80), nullable=False)
    breed: Mapped[str] = mapped_column(String(120), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[AnimalStatus] = mapped_column(
        _enum_column(AnimalStatus, "animal_status"),
        nullable=False,
        default=AnimalStatus.AVAILABLE,
    )
    shelter_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("shelters.id"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    shelter: Mapped[Shelter] = relationship(back_populates="animals")
    applications: Mapped[list[ShelterApplication]] = relationship(
        back_populates="animal", cascade="all, delete-orphan"
    )

    @property
    def is_available(self) -> bool:
        return self.status is AnimalStatus.AVAILABLE

    def open_applications(self) -> list[ShelterApplication]:
        """Applications still awaiting a staff decision."""
        return [app for app in self.applications if app.is_open]

    def __repr__(self) -> str:
        return f"<Animal id={self.id} name={self.name!r} status={self.status.value}>"


class ShelterApplication(Base):
    """An adopter's request to adopt one animal."""

    __tablename__ = "shelter_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    adopter_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    animal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("animals.id"), nullable=False, index=True
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        _enum_column(ApplicationStatus, "application_status"),
        nullable=False,
        default=ApplicationStatus.PENDING,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    adopter: Mapped[Adopter] = relationship(back_populates="applications")
    animal: Mapped[Animal] = relationship(back_populates="applications")

    @property
    def is_open(self) -> bool:
        """True while the application still awaits a decision."""
        return self.status is ApplicationStatus.PENDING

    def __repr__(self) -> str:
        return (
            f"<ShelterApplication id={self.id} adopter_id={self.adopter_id} "
            f"animal_id={self.animal_id} status={self.status.value}>"
        )

"""Password hashing, JWT issuing/verification, and role-based access control."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import Adopter, Staff, User, UserRole

#: Local-development fallback only. At least 32 bytes, which is the minimum
#: HMAC-SHA256 key length PyJWT accepts without warning.
SECRET_KEY = os.getenv(
    "SECRET_KEY", "dev-only-insecure-secret-change-me-before-deploying"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
#: bcrypt work factor. Lowered only by the test suite, never in deployment.
BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))

_bearer = HTTPBearer(auto_error=False)

_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


# ---------------------------------------------------------------- passwords ---
def hash_password(password: str) -> str:
    """Hash a plaintext password with a per-password bcrypt salt."""
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except (ValueError, TypeError):
        # Malformed/legacy hash in the database -- never leak it as a 500.
        return False


# --------------------------------------------------------------------- JWT ----
def create_access_token(user: User) -> str:
    """Issue a signed HS256 access token for ``user``."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Verify signature and expiry, returning the token claims."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise _CREDENTIALS_ERROR from None


# ------------------------------------------------------------ dependencies ----
def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the bearer token to a persisted :class:`User`.

    Returns the concrete subtype (``Staff`` or ``Adopter``) thanks to the
    polymorphic mapping, so callers can rely on ``isinstance``.
    """
    if credentials is None or not credentials.credentials:
        raise _CREDENTIALS_ERROR

    subject = decode_access_token(credentials.credentials).get("sub")
    if subject is None:
        raise _CREDENTIALS_ERROR
    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        raise _CREDENTIALS_ERROR from None

    user = db.get(User, user_id)
    if user is None:
        raise _CREDENTIALS_ERROR
    return user


def require_staff(current_user: User = Depends(get_current_user)) -> Staff:
    """Allow only shelter staff through."""
    if not isinstance(current_user, Staff):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This action requires the '{UserRole.STAFF.value}' role",
        )
    return current_user


def require_adopter(current_user: User = Depends(get_current_user)) -> Adopter:
    """Allow only adopters through."""
    if not isinstance(current_user, Adopter):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This action requires the '{UserRole.ADOPTER.value}' role",
        )
    return current_user

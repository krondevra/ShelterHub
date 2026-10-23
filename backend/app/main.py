"""ShelterHub API application factory and wiring."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routers import animals, applications, auth, shelters
from .uploads import UPLOAD_DIR, ensure_upload_dirs

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]

# The schema comes from Alembic migrations and the shelters from app.seed; the
# Docker entrypoint runs both before starting the server (see entrypoint.sh).
app = FastAPI(title="ShelterHub API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(animals.router)
app.include_router(applications.router)
app.include_router(shelters.router)

# Animal photos. The directory is created at import time because StaticFiles
# checks that it exists as soon as it is constructed.
ensure_upload_dirs()
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}

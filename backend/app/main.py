"""ShelterHub API application factory and wiring."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, SessionLocal, engine
from .routers import animals, applications, auth, shelters
from .seed import seed_shelters

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables and seed demo shelters on startup.

    The project has no migration tool, so the schema is created from the
    model metadata. Swap this for Alembic if the schema starts changing.
    """
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_shelters(db)
    yield


app = FastAPI(title="ShelterHub API", lifespan=lifespan)

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


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}

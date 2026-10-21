#!/usr/bin/env python3
"""End-to-end smoke check against a running ShelterHub API.

Exercises the whole contract against whatever database the app is actually
wired to, which is what makes it useful in Docker: the pytest suite always runs
on SQLite, so this is the only thing that proves the stack works on PostgreSQL.

Usage, from inside the backend container:

    docker compose exec backend python scripts/smoke_check.py

Or against any reachable deployment:

    python scripts/smoke_check.py http://localhost:8000

Exits non-zero if any check fails.
"""

from __future__ import annotations

import pathlib
import sys
import uuid
from datetime import datetime

import httpx

# Running this as `python scripts/smoke_check.py` puts scripts/ on sys.path,
# not the backend root -- add it so the `app` package can be inspected.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

BASE_URL = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")
PASSWORD = "password123"

_results: list[tuple[bool, str, str]] = []


def check(ok: bool, name: str, detail: str = "") -> bool:
    _results.append((bool(ok), name, detail))
    return bool(ok)


def describe_database() -> str:
    """Report the database the *app* is using, with the password masked."""
    try:
        from app.database import DATABASE_URL
    except Exception:  # noqa: BLE001 - cosmetic only; never fail the run over it
        return "unknown (run inside the backend container to detect)"
    url = DATABASE_URL
    if "://" in url and "@" in url:
        scheme, rest = url.split("://", 1)
        creds, host = rest.rsplit("@", 1)
        user = creds.split(":", 1)[0]
        url = f"{scheme}://{user}:***@{host}"
    return url


def main() -> int:
    suffix = uuid.uuid4().hex[:8]
    staff_email = f"smoke-staff-{suffix}@example.com"
    adopter_email = f"smoke-adopter-{suffix}@example.com"

    print(f"target   : {BASE_URL}")
    print(f"database : {describe_database()}\n")

    with httpx.Client(base_url=BASE_URL, timeout=20.0) as c:
        # --- reachability -------------------------------------------------
        r = c.get("/health")
        if not check(r.status_code == 200, "GET /health", f"-> {r.status_code}"):
            return report()

        # --- seeded shelters ----------------------------------------------
        r = c.get("/shelters")
        shelters = r.json() if r.status_code == 200 else []
        check(
            r.status_code == 200 and len(shelters) > 0,
            "GET /shelters returns seeded data",
            f"-> {len(shelters)} shelter(s)",
        )
        if not shelters:
            return report()
        shelter_id = shelters[0]["id"]

        # --- registration --------------------------------------------------
        def register(email: str, role: str):
            return c.post(
                "/auth/register",
                json={"email": email, "password": PASSWORD, "role": role},
            )

        r = register(staff_email, "staff")
        check(
            r.status_code == 201 and set(r.json()) == {"id", "email", "role"},
            "POST /auth/register (staff)",
            f"-> {r.status_code}",
        )
        r = register(adopter_email, "adopter")
        check(
            r.status_code == 201, "POST /auth/register (adopter)", f"-> {r.status_code}"
        )
        check(
            register(staff_email, "staff").status_code == 409,
            "duplicate email rejected",
            "-> 409",
        )

        # --- login ----------------------------------------------------------
        def token(email: str) -> str | None:
            r = c.post("/auth/login", json={"email": email, "password": PASSWORD})
            return r.json().get("access_token") if r.status_code == 200 else None

        staff_token, adopter_token = token(staff_email), token(adopter_email)
        if not check(
            bool(staff_token and adopter_token), "POST /auth/login issues tokens"
        ):
            return report()
        staff = {"Authorization": f"Bearer {staff_token}"}
        adopter = {"Authorization": f"Bearer {adopter_token}"}

        check(
            c.post(
                "/auth/login", json={"email": staff_email, "password": "wrong"}
            ).status_code
            == 401,
            "bad password rejected",
            "-> 401",
        )

        # --- role enforcement ------------------------------------------------
        animal_body = {
            "name": "SmokeRex",
            "species": "dog",
            "breed": "labrador",
            "age": 3,
            "shelter_id": shelter_id,
        }
        check(
            c.post("/animals", json=animal_body).status_code == 401,
            "unauthenticated write rejected",
            "-> 401",
        )
        check(
            c.post("/animals", json=animal_body, headers=adopter).status_code == 403,
            "adopter blocked from staff route",
            "-> 403",
        )

        # --- create animal ---------------------------------------------------
        r = c.post("/animals", json=animal_body, headers=staff)
        if not check(
            r.status_code == 201,
            "POST /animals (staff)",
            f"-> {r.status_code} {r.text[:80]}",
        ):
            return report()
        animal = r.json()
        animal_id = animal["id"]
        check(
            set(animal)
            == {"id", "name", "species", "breed", "age", "status", "shelter_id"},
            "animal matches contract fields",
            f"-> {sorted(animal)}",
        )
        check(animal["status"] == "available", "new animal is 'available'")

        def animal_status() -> str:
            return c.get(f"/animals/{animal_id}").json()["status"]

        # --- apply -------------------------------------------------------------
        r = c.post("/applications", json={"animal_id": animal_id}, headers=adopter)
        if not check(
            r.status_code == 201,
            "POST /applications (adopter)",
            f"-> {r.status_code}"
            if r.status_code == 201
            else f"-> {r.status_code} {r.text[:120]}",
        ):
            return report()
        application = r.json()
        check(
            set(application)
            == {"id", "adopter_id", "animal_id", "status", "created_at"},
            "application matches contract fields",
            f"-> {sorted(application)}",
        )
        check(application["status"] == "pending", "new application is 'pending'")
        check(animal_status() == "pending", "animal moved to 'pending'")

        # The interesting database-dependent bit: PostgreSQL's timestamptz
        # round-trips an offset, SQLite does not.
        created = application["created_at"]
        parsed = datetime.fromisoformat(created)
        check(True, "created_at parses as ISO-8601", f"-> {created}")
        print(
            f"   note   : created_at is "
            f"{'timezone-aware (PostgreSQL timestamptz)' if parsed.tzinfo else 'naive (SQLite, or a naive column)'}"
        )

        # --- approve -----------------------------------------------------------
        r = c.patch(
            f"/applications/{application['id']}",
            json={"status": "approved"},
            headers=staff,
        )
        check(
            r.status_code == 200 and r.json()["status"] == "approved",
            "PATCH /applications approves",
            f"-> {r.status_code}",
        )
        check(animal_status() == "adopted", "approval auto-adopts the animal")
        check(
            c.post(
                "/applications", json={"animal_id": animal_id}, headers=adopter
            ).status_code
            == 409,
            "adopted animal rejects new applications",
            "-> 409",
        )

        # --- scoping -------------------------------------------------------------
        mine = c.get("/applications", headers=adopter).json()
        everything = c.get("/applications", headers=staff).json()
        check(
            all(a["adopter_id"] == application["adopter_id"] for a in mine),
            "adopter sees only their own applications",
            f"-> {len(mine)} row(s)",
        )
        check(
            len(everything) >= len(mine),
            "staff see all applications",
            f"-> {len(everything)} row(s)",
        )

    return report()


def report() -> int:
    print()
    failures = 0
    for ok, name, detail in _results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name} {detail}".rstrip())
        failures += not ok
    total = len(_results)
    print(f"\n{total - failures}/{total} checks passed")
    if failures:
        print(f"{failures} FAILED")
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except httpx.HTTPError as exc:
        print(f"\nCould not reach {BASE_URL}: {exc}")
        print("Is the stack up?  docker compose ps")
        sys.exit(2)

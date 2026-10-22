# Backend Decisions

Everything the backend does that [API_CONTRACT.md](API_CONTRACT.md) does **not**
specify. The contract stays the source of truth — this file records the gaps that
had to be filled to make it runnable, so the team can accept, reject, or fold
them into the contract.

> **Accepted into the contract:** items [1](#1-get-shelters),
> [2](#2-an-application-moves-its-animal-to-pending) and
> [3](#3-who-may-apply-for-which-animal) were signed off by the team and are
> now part of [API_CONTRACT.md](API_CONTRACT.md). Rules 4–7, the password
> length and the main status codes were written into the contract at the same
> time. They are kept here for the reasoning behind them; wherever the two
> documents overlap, the contract wins.

---

## Endpoints

### 1. `GET /shelters`

*Accepted into the contract.*

**Added** — public, read-only, returns `[{ "id": int, "name": str, "city": str | null }]`.

The original contract defined no endpoint that creates *or* lists shelters, yet
`POST /animals` requires a `shelter_id`. Without this, the frontend has no way
to discover a valid shelter id. Three demo shelters are seeded on startup
(see [13](#13-schema-creation-and-seeding)).

No `POST /shelters` was added: creating shelters is not in scope for any
documented user story, and adding a write endpoint is a bigger contract change
than the team agreed to.

---

## Status flow

The original contract only stated that approving an application sets
`Animal.status = "adopted"`; the rest of the `available -> pending -> adopted`
lifecycle was defined here first. The contract now spells out rules 2–7, and
rule 8 follows from the same decision: an animal's status changes only through
applications.

### 2. An application moves its animal to `pending`

*Accepted into the contract.*

`POST /applications` sets the animal's status to `pending` if it was
`available`. Without this rule the `"pending"` animal status in the contract is
unreachable and the three-state flow is really a two-state one.

### 3. Who may apply for which animal

*Accepted into the contract.*

| Animal status | New application? |
|---|---|
| `available` | yes — animal becomes `pending` |
| `pending`   | yes — adopters compete for the same animal |
| `adopted`   | **409** `Animal {id} has already been adopted` |

Applying to a `pending` animal is deliberately allowed. Blocking it would mean
the first applicant silently locks out everyone else, which is not how a shelter
works and would make rule [5](#5-approving-rejects-the-competing-applications)
dead code.

### 4. One open application per adopter per animal

A second application from the same adopter for the same animal is **409**
`You already have a pending application for animal {id}`. Checked *before* the
status rule so a repeat applicant gets the precise reason. Re-applying after a
rejection is allowed — the constraint is on *open* applications only, which is
why there is no database-level unique constraint on
`(adopter_id, animal_id)`.

### 5. Approving rejects the competing applications

When staff approve one application, every other still-open application for that
animal is set to `rejected`. Otherwise they would hang as `pending` forever
against an animal nobody can adopt.

### 6. Rejecting the last open application frees the animal

Rejecting an application returns the animal to `available` **only if** the
animal is currently `pending` and no other open application remains. An animal
that is already `adopted` is never reverted.

### 7. A decision is final

`PATCH /applications/{id}` on an already approved/rejected application is
**409**. The schema also refuses `{"status": "pending"}`, so an application
cannot be reopened.

### 8. `PATCH /animals/{id}` does not accept `status`

The contract lists the patchable fields: `name`, `species`, `breed`, `age` and
`shelter_id`. `status` is not among them. It is driven only by the application
flow (rules 2, 3, 5 and 6), so the status shown for an animal can never
disagree with its applications. Sending `status` is a **422**, like any other
field the endpoint does not know (see [Validation](#validation)).

`status` sent to `POST /animals` is ignored rather than rejected: the contract
fixes the initial value at `"available"`.

---

## Status codes

The contract fixes the error *body* (`{"detail": str}`) and now lists the codes
too. This table records the exact cases behind them.

| Situation | Code |
|---|---|
| Duplicate email on register | `409` |
| Wrong password **or** unknown email on login | `401`, identical message both ways so the endpoint cannot be used to enumerate accounts |
| Missing, malformed, or expired token | `401` |
| Authenticated but wrong role | `403` |
| Unknown animal / application / shelter | `404` |
| `shelter_id` pointing at no shelter (`POST`/`PATCH /animals`) | `404` — treated as an unknown resource rather than a malformed body |
| Schema validation failure | `422` (FastAPI's default; body is still `{"detail": ...}`) |

---

## Validation

The contract types fields and, apart from the password length, states no
constraints. Added:

- **email** — validated as a real address (`EmailStr`) and lower-cased before
  storing and before lookup, so `Alice@x.com` and `alice@x.com` are one account.
- **password** — 8–72 characters, and at most 72 bytes once UTF-8 encoded.
  The upper bound is bcrypt's and is counted in bytes, so the two only differ
  for non-ASCII passwords: 40 Cyrillic letters are 80 bytes and are rejected
  (`422`).
- **age** — `>= 0`, enforced both in Pydantic and by a database `CHECK`, and
  at most 2147483647, the largest value the `INTEGER` column holds.
- **name / species / breed** — non-empty, with column-width maximums.
- **PATCH bodies** — unknown fields are rejected (`422`); on
  `PATCH /animals/{id}` that includes `status`
  (see [8](#8-patch-animalsid-does-not-accept-status)). A field is either sent
  with a value or left out: an explicit `null` is a `422` as well. An empty
  `{}` patch is a no-op that returns `200` with the unchanged object.

---

## Auth mechanics

- **9. Tokens** — HS256 JWT, sent as `Authorization: Bearer <token>`. Claims:
  `sub` (user id as a string), `role`, `iat`, `exp`. Lifetime 60 minutes,
  configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`.
- **10. Passwords** — bcrypt with a per-password salt. The work factor is
  `BCRYPT_ROUNDS` (12 in deployment, 4 in tests so the suite is not bcrypt-bound).
- **11. Which routes are public** — `GET /animals`, `GET /animals/{id}`,
  `GET /shelters` and `/health` need no token; the contract marks no role on
  them. `GET /applications` requires one, since it must tell staff from adopter.

---

## Domain model

- **12. Single-table inheritance** — `User`/`Staff`/`Adopter` share the `users`
  table, discriminated by `users.role`, which is the same `role` the contract
  exposes. Full rationale and diagram in [UML_MODELS.md](UML_MODELS.md).
- `created_at` is stored offset-aware in UTC. PostgreSQL returns it with a
  `+00:00` offset; SQLite (tests only) drops the offset on read-back. Both are
  valid ISO-8601, which is all the contract requires of `created_at: str`.

---

## Infrastructure

### 13. Schema creation and seeding

`Base.metadata.create_all()` runs on startup — the project has no migration
tool. **If the models change after the database exists, the schema will not
update**; drop the `pgdata` volume or add Alembic. Three demo shelters are
inserted on startup when the `shelters` table is empty.

Both are temporary. Alembic migrations and a standalone seed script are planned
(owned by DevOps) and will replace this startup hook. Existing databases
need the new `animals.photo_path` column (see 15) until then.

### 14. CORS

Enabled for `http://localhost:5173` and `http://127.0.0.1:5173`, overridable via
`CORS_ORIGINS`. The browser will not let the frontend call the API without it.

### 15. Animal photos

`POST /animals/{id}/photo` stores the file on disk under `UPLOAD_DIR/animals`
(`backend/uploads` by default, a named `uploads` volume in Docker); the
database only keeps the file name in `animals.photo_path`. Files are saved
under a new random name (`<animal id>-<uuid>.<ext>`), never the client's file
name. The format is checked from the file's first bytes (JPEG, PNG, WebP
signatures), not from the name or the client's Content-Type. The upload is
read in chunks and refused with 413 as soon as it passes 5 MB. Replacing or
deleting a photo removes the old file after the database commit.

With this change `AnimalCreate` also forbids unknown fields, so sending
`status` or `photo_url` to `POST /animals` is a 422 instead of being ignored,
the same as for `PATCH`.

### 16. Dependency versions

Pins were raised so one set of versions works on both Python 3.12 (the Docker
image) and 3.14 (local test runs). The original `pydantic==2.9.2` has no wheel
for 3.14 and fails to build from source. `pytest` and `httpx` are in
`requirements.txt` rather than a separate dev file so that
`docker compose exec backend pytest` works without a second install step.

---

## Known gaps

Not bugs — consequences of the contract as written. Flagged for the team.

1. **Anyone can register as staff.** `POST /auth/register` accepts
   `role: "staff"` from an unauthenticated caller, so any visitor can grant
   themselves write access to animals and applications. Implemented as
   specified. A real deployment needs an invite code, an admin-only creation
   route, or staff seeded out of band.
2. **Staff are not scoped to a shelter.** `Staff.shelter_id` exists in the model
   but no endpoint ever sets it, so any staff member can edit any shelter's
   animals. The contract provides no way to assign staff to a shelter.
3. **No delete.** The contract defines no `DELETE` route, so animals and
   applications cannot be removed through the API.
4. **No pagination.** `GET /animals` and `GET /applications` return everything.
5. **No `GET /auth/me`.** The frontend must decode the JWT or remember the
   register response to know the current user's role.
6. **No manual status correction.** `PATCH /animals/{id}` does not accept
   `status` and a decision on an application is final, so an approval made by
   mistake cannot be undone through the API, and an animal that leaves the
   shelter outside the application flow cannot be marked `adopted` without an
   application.

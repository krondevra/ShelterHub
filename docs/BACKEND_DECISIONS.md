# Backend Decisions

Everything the backend does that [API_CONTRACT.md](API_CONTRACT.md) does **not**
specify. The contract stays the source of truth — this file records the gaps that
had to be filled to make it runnable, so the team can accept, reject, or fold
them into the contract.

> **Needs team sign-off before the contract is updated:** items
> [1](#1-get-shelters), [2](#2-an-application-moves-its-animal-to-pending) and
> [3](#3-who-may-apply-for-which-animal). Everything else is an implementation
> detail that does not change the documented request/response shapes.

---

## Endpoints

### 1. `GET /shelters`

**Added** — public, read-only, returns `[{ "id": int, "name": str, "city": str | null }]`.

The contract defines no endpoint that creates *or* lists shelters, yet
`POST /animals` requires a `shelter_id`. Without this, the frontend has no way
to discover a valid shelter id. Three demo shelters are seeded on startup
(see [13](#13-schema-creation-and-seeding)).

No `POST /shelters` was added: creating shelters is not in scope for any
documented user story, and adding a write endpoint is a bigger contract change
than the team agreed to.

---

## Status flow

The contract only states that approving an application sets
`Animal.status = "adopted"`. The rest of the `available -> pending -> adopted`
lifecycle is defined here.

### 2. An application moves its animal to `pending`

`POST /applications` sets the animal's status to `pending` if it was
`available`. Without this rule the `"pending"` animal status in the contract is
unreachable and the three-state flow is really a two-state one.

### 3. Who may apply for which animal

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

### 8. `PATCH /animals/{id}` accepts `status`

The contract says "partial fields to update" without listing them. The patchable
set is `name`, `species`, `breed`, `age`, `status`, `shelter_id` — i.e. every
mutable field. This is the escape hatch staff use to correct a status by hand.
`status` sent to `POST /animals` is ignored: the contract fixes the initial
value at `"available"`.

---

## Status codes

The contract fixes the error *body* (`{"detail": str}`) but not the codes.

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

The contract types fields but states no constraints. Added:

- **email** — validated as a real address (`EmailStr`) and lower-cased before
  storing and before lookup, so `Alice@x.com` and `alice@x.com` are one account.
- **password** — 8–72 characters. The upper bound is bcrypt's: it silently
  ignores anything past 72 bytes, so it is rejected instead.
- **age** — `>= 0`, enforced both in Pydantic and by a database `CHECK`.
- **name / species / breed** — non-empty, with column-width maximums.
- **PATCH bodies** — unknown fields are rejected (`422`). An empty `{}` patch is
  a no-op that returns `200` with the unchanged object.

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

### 14. CORS

Enabled for `http://localhost:5173` and `http://127.0.0.1:5173`, overridable via
`CORS_ORIGINS`. The browser will not let the frontend call the API without it.

### 15. Dependency versions

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

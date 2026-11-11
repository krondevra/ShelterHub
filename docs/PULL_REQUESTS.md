# Pull requests

All work reached `main` through pull requests with a review, except a few small
contract updates. The table below lists PRs #1-#11 from the three sprints; each
one is a `Merge pull request #N` commit on `main`, up to commit `2f720fa`. The
PRs after that are numbered again from #1, see
[Final pull requests](#final-pull-requests).

| # | Title | Author | Reviewed by | Opened | Merged |
|---|-------|--------|-------------|--------|--------|
| 1 | Add backend domain models, JWT auth, CRUD routes and tests | gospacho19 | krondevra | 2026-09-26 | 2026-10-21 |
| 2 | Add frontend: API hooks, routing, auth, adoption flow, staff panel | bebrraa | krondevra | 2026-10-22 | 2026-10-22 |
| 3 | Review fixes + UI polish | bebrraa | krondevra | 2026-10-22 | 2026-10-22 |
| 4 | Animal photo upload (frontend) | bebrraa | krondevra | 2026-10-22 | 2026-10-22 |
| 5 | Keep Apply state and animal list visible during refetch | krondevra | - | 2026-10-22 | 2026-10-22 |
| 6 | Animal photo upload and delete (backend) | krondevra | - | 2026-10-22 | 2026-10-22 |
| 7 | Retry new animal photos and free preview memory | krondevra | - | 2026-10-22 | 2026-10-22 |
| 8 | Alembic migrations, demo seed and migrate-on-start | krondevra | - | 2026-10-23 | 2026-10-23 |
| 9 | CI: tests on SQLite and PostgreSQL, frontend build, Docker smoke test | krondevra | - | 2026-10-23 | 2026-10-23 |
| 10 | Playwright browser tests (Chromium + Firefox) in CI | krondevra | - | 2026-10-23 | 2026-10-23 |
| 11 | Database docs and README update | krondevra | - | 2026-10-23 | 2026-10-23 |

## Backend

**#1 Backend domain models, JWT auth, CRUD routes and tests** (gospacho19)

Domain models with `User` as a base class for `Staff` and `Adopter` (single-table
inheritance), plus `Shelter`, `Animal` and `ShelterApplication`. JWT auth with bcrypt
and role checks, all ten routes from the API contract, and the
`available -> pending -> adopted` flow driven only by applications. 98 pytest tests.

Review: the first review asked to merge the updated contract from `main`, remove
`status` from `PATCH /animals/{id}` (status only changes through applications),
update `BACKEND_DECISIONS.md` and leave a note that Alembic will replace
`create_all()`. All of it was fixed, plus three inputs that returned 500 now return
422 (`null` in PATCH, password over 72 bytes, `age` out of range). Approved after
re-review with 98 tests passing.

**#6 Animal photo upload and delete** (krondevra)

`POST /animals/{id}/photo` and `DELETE /animals/{id}/photo` for staff, JPEG/PNG/WebP
up to 5 MB, file type checked from the first bytes. Every animal response got
`photo_url`. 15 new tests, 114 passing.

## Frontend

**#2 API hooks, routing, auth, adoption flow, staff panel** (bebrraa)

Hooks for auth, animals and applications, React Router pages, registration and
login, the adopter application flow and the staff panel (animal CRUD, approve or
reject applications). Zod validation that mirrors the backend rules, 34 Vitest tests.

Review: tests and build checked locally, matched against the contract. Four inline
comments, none blocking:

- `useQuery` set `loading` back to true on every refetch, so the tables flickered.
- `useAuth` didn't check the token `exp`, so an expired token still looked logged in.
- Animal form validation missed the backend max lengths (120 / 80 / 120).
- The "applied" state was only in local state and was lost after a reload.

Approved and merged, with the fixes to be done in a new branch.

**#3 Review fixes + UI polish** (bebrraa)

All four comments from #2 fixed, plus UI work: species icons on cards, consistent
button styles, active page highlighting, spinner, empty states, and a missing
viewport meta tag that broke the layout on phones. Approved.

**#4 Animal photo upload** (bebrraa)

Photo picker with preview and client-side type/size checks in the staff panel,
photos on animal cards with a fallback icon. Built against the agreed contract
before the backend existed, so it waited for #6. Approved after checking it
locally against the backend from #6.

**#5 and #7** (krondevra): small follow-ups to #3 and #4. The Apply button no longer
comes back for a moment after applying, a failed refetch keeps the old list on
screen, a new photo is retried after an earlier one failed to load, and preview
`blob:` URLs are released.

## DevOps and QA

**#8 Alembic migrations, demo seed and migrate-on-start** (krondevra)

Alembic with one baseline revision, CHECK constraints for the status columns,
`python -m app.seed` with an optional `--demo` data set, and an entrypoint that runs
migrations and the seed before starting the API. Tests for migrations and seed.

**#9 CI** (krondevra)

GitHub Actions: backend tests on SQLite, backend tests and migration checks on
PostgreSQL, frontend tests and build, Docker Compose smoke test.

**#10 Playwright browser tests** (krondevra)

End-to-end tests in Chromium and Firefox: the full adoption flow, access rules,
adding an animal with a photo, and register form validation. Runs in CI against the
Compose stack.

**#11 Database docs and README update** (krondevra)

`docs/DATABASE.md` with the ER diagram and table descriptions, and the README
sections on setup, demo accounts, tests and configuration.

## Final pull requests

| # | Title | Author | Merged |
|---|-------|--------|--------|
| 1 | Add team and roles to README | krondevra | 2026-11-11 |
| 2 | Add full photo view and tidy up animal cards | krondevra | 2026-11-11 |
| 3 | Add photos to the demo animals | krondevra | 2026-11-11 |

**#1 Team and roles:** a README section on who is in the team and what each
person built.

**#2 Full photo view:** clicking an animal photo opens it full size. The card
picture area is 4:3 instead of a thin strip, the Species / Breed / Age labels
sit above the values, and Choose photo in the staff panel looks like a button.
4 new frontend tests.

**#3 Demo photos:** each demo animal gets a photo of its breed from Wikimedia
Commons (free licenses, credits in `backend/app/demo_photos/CREDITS.md`). The seed
copies them into the upload folder like normal uploads. 3 new backend tests.

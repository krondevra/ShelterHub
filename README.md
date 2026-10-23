# ShelterHub

[![CI](https://github.com/krondevra/ShelterHub/actions/workflows/ci.yml/badge.svg)](https://github.com/krondevra/ShelterHub/actions/workflows/ci.yml)

Animal shelter registration and adoption system. University group project built
with FastAPI (backend), React (frontend), and PostgreSQL (database).

Visitors browse the animals of three shelters, adopters apply to adopt, and
shelter staff manage animals (with photos) and approve or reject applications.

## Stack

- **Backend:** FastAPI, SQLAlchemy, Alembic, PostgreSQL driver (psycopg2)
- **Frontend:** React (Vite), React Router, Zod
- **Database:** PostgreSQL 16
- **Orchestration:** Docker Compose
- **Tests and CI:** pytest, Vitest + React Testing Library, Playwright, GitHub Actions

## Run with Docker

Prerequisites: Docker and Docker Compose.

```bash
git clone https://github.com/krondevra/ShelterHub.git
cd ShelterHub
docker compose up --build
```

| Service  | URL                        |
|----------|----------------------------|
| frontend | http://localhost:5173      |
| backend  | http://localhost:8000 (API docs at `/docs`) |
| db       | localhost:5432             |

On start the backend applies the database migrations and seeds three shelters
plus demo data (`backend/entrypoint.sh`). Demo accounts, all with the password
`password123`:

| Email | Role |
|---|---|
| `staff@example.com` | staff |
| `anna@example.com` | adopter |
| `janis@example.com` | adopter |

Set `SEED_DEMO=0` to start without the demo data. Uploaded photos are kept in the
`uploads` volume, the database in `pgdata` (`docker compose down -v` removes both).

## Run without Docker

Uses SQLite instead of PostgreSQL. Backend (Python 3.12+):

```bash
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=sqlite:///./dev.db SECRET_KEY=dev-secret-at-least-32-bytes-long-123
alembic upgrade head
python -m app.seed --demo
uvicorn app.main:app --reload
```

Frontend (Node 20+), in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

## Tests

| What | Command | Notes |
|---|---|---|
| Backend | `cd backend && pytest` | in-memory SQLite; set `TEST_DATABASE_URL` to run on PostgreSQL |
| Frontend | `cd frontend && npm test` | Vitest + React Testing Library |
| Browser (E2E) | `cd frontend && npx playwright install chromium firefox && npm run e2e` | needs the stack running with the demo seed |
| Smoke check | `docker compose exec backend python scripts/smoke_check.py` | whole API against the running database |

GitHub Actions runs all of them on every pull request: backend tests on SQLite
and PostgreSQL (plus a migration check), frontend tests and build, a Docker
Compose smoke test, and the Playwright tests in Chromium and Firefox.

## Configuration

Backend settings are environment variables; see `backend/.env.example`.

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | PostgreSQL in Compose | database connection |
| `SECRET_KEY` | dev-only value | JWT signing key, change outside local development |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 60 | login lifetime |
| `CORS_ORIGINS` | `http://localhost:5173,...` | origins allowed to call the API |
| `UPLOAD_DIR` | `backend/uploads` | where animal photos are stored |
| `SEED_DEMO` | `1` in Compose | add demo data on container start |
| `VITE_API_URL` (frontend) | `http://localhost:8000` | API base URL |

## Project structure

```
ShelterHub/
├── backend/          # FastAPI app, Alembic migrations, tests, entrypoint
├── frontend/         # React app, unit tests, Playwright tests (e2e/)
├── docs/             # API contract, database, UML, backend decisions
├── .github/workflows # CI
└── docker-compose.yml
```

## Documentation

- [API contract](docs/API_CONTRACT.md): endpoints and request/response formats
- [Database](docs/DATABASE.md): ER diagram, tables, migrations and seed
- [UML models](docs/UML_MODELS.md): class diagram and status lifecycles
- [Backend decisions](docs/BACKEND_DECISIONS.md): design choices and known gaps

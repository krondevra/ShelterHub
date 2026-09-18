# ShelterHub

Animal shelter registration and adoption system. University group project built
with FastAPI (backend), React (frontend), and PostgreSQL (database).

## Stack

- **Backend:** FastAPI, SQLAlchemy, PostgreSQL driver (psycopg2)
- **Frontend:** React (Vite)
- **Database:** PostgreSQL 16
- **Orchestration:** Docker Compose

## Setup

### Prerequisites

- Docker and Docker Compose

### Run the project

```bash
git clone https://github.com/krondevra/ShelterHub.git
cd ShelterHub
docker compose up --build
```

This starts three services:

| Service  | URL                      |
|----------|--------------------------|
| backend  | http://localhost:8000    |
| frontend | http://localhost:5173    |
| db       | localhost:5432           |

Check the backend is up:

```bash
curl http://localhost:8000/health
```

### Environment variables

Copy `backend/.env.example` to `backend/.env` and adjust if you need a
non-default database connection string.

## Project structure

```
ShelterHub/
├── backend/     # FastAPI application
├── frontend/    # React application
├── docs/        # Project documentation
└── docker-compose.yml
```

## API Contract

See [docs/API_CONTRACT.md](docs/API_CONTRACT.md) for endpoint definitions and
request/response schemas.

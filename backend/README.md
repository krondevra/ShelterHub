# ShelterHub Backend

FastAPI + SQLAlchemy implementation of [docs/API_CONTRACT.md](../docs/API_CONTRACT.md).

Behaviour the contract does not specify is recorded in
[docs/BACKEND_DECISIONS.md](../docs/BACKEND_DECISIONS.md); the model layer is
diagrammed in [docs/UML_MODELS.md](../docs/UML_MODELS.md).

## Layout

```
app/
├── main.py         # app wiring: CORS, routers, startup (create tables + seed)
├── database.py     # engine / SessionLocal / Base / get_db
├── models.py       # User -> Staff|Adopter, Shelter, Animal, ShelterApplication
├── schemas.py      # Pydantic request/response models
├── security.py     # password hashing, JWT, role dependencies
├── seed.py         # demo shelters
└── routers/        # auth, animals, applications, shelters
tests/              # pytest suite, runs on in-memory SQLite
```

## Running

With the rest of the stack:

```bash
docker compose up --build
```

Interactive API docs: <http://localhost:8000/docs>.

## Tests

The suite never touches PostgreSQL — each test gets a fresh in-memory SQLite
database and the `get_db` dependency is overridden to point at it.

In the container:

```bash
docker compose exec backend pytest
```

Or locally, without Docker:

```bash
cd backend && python -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/pytest
```

## Trying it by hand

```bash
curl -s localhost:8000/shelters
curl -s -X POST localhost:8000/auth/register -H 'content-type: application/json' \
  -d '{"email":"staff@example.com","password":"password123","role":"staff"}'
TOKEN=$(curl -s -X POST localhost:8000/auth/login -H 'content-type: application/json' \
  -d '{"email":"staff@example.com","password":"password123"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
curl -s -X POST localhost:8000/animals -H "authorization: Bearer $TOKEN" \
  -H 'content-type: application/json' \
  -d '{"name":"Rex","species":"dog","breed":"labrador","age":3,"shelter_id":1}'
```

## Configuration

See [`.env.example`](.env.example). `SECRET_KEY` must be overridden anywhere
that is not local development.

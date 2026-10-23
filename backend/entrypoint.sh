#!/bin/sh
# Container start: bring the database schema up to date, seed it, then run the API.
set -e

alembic upgrade head

# SEED_DEMO=1 also adds demo accounts, animals and applications (only once).
if [ "${SEED_DEMO:-0}" = "1" ]; then
    python -m app.seed --demo
else
    python -m app.seed
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

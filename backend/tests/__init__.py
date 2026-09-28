"""Test package.

Environment defaults live here rather than in ``conftest.py``: this module is
imported before conftest, and therefore before any application module reads
configuration at import time.

``DATABASE_URL`` is forced rather than defaulted. Inside the Docker container
the real PostgreSQL URL is already in the environment, and ``setdefault`` would
leave it in place -- so an overwrite is what actually guarantees that
``docker compose exec backend pytest`` can never reach the live database.
"""

import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ.setdefault("SECRET_KEY", "test-secret-at-least-32-bytes-long-for-hs256")
# Cheapest legal bcrypt cost -- the suite registers a lot of users.
os.environ.setdefault("BCRYPT_ROUNDS", "4")

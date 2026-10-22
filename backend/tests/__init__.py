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
import tempfile

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
# Forced for the same reason: uploaded test photos must never land in the real
# uploads folder (or the Docker volume).
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp(prefix="shelterhub-test-uploads-")
os.environ.setdefault("SECRET_KEY", "test-secret-at-least-32-bytes-long-for-hs256")
# Cheapest legal bcrypt cost -- the suite registers a lot of users.
os.environ.setdefault("BCRYPT_ROUNDS", "4")

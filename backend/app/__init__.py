"""ShelterHub backend application package.

Loading ``.env`` here means it happens before any submodule reads configuration
via ``os.getenv``. ``load_dotenv`` does not overwrite variables that are already
set, so real environment variables -- those from ``docker-compose.yml``, or the
ones the test suite sets in ``tests/__init__.py`` -- always win over the file.
"""

from dotenv import load_dotenv

load_dotenv()

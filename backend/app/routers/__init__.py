"""API route modules, one per resource group in docs/API_CONTRACT.md."""

from . import animals, applications, auth, shelters

__all__ = ["animals", "applications", "auth", "shelters"]

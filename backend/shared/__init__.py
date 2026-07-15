"""Shared utilities and base classes for all services."""
from shared.config import settings
from shared.database import Base, get_db, get_db_session, engine
from shared import schemas  # noqa: F401 — re-export for convenience

__all__ = ["settings", "Base", "get_db", "get_db_session", "engine", "schemas"]
"""SQLite connection helpers and schema initialization."""

from __future__ import annotations

from pathlib import Path

from data.db import (
    DB_PATH,
    ensure_bootstrap,
    get_connection as _get_connection,
    init_db as _init_db,
    test_connection,
)


def get_connection(db_path: Path | None = None):
    """Return a managed SQLite connection (backwards compatible import)."""
    ensure_bootstrap(db_path=db_path)
    return _get_connection(db_path)


def init_db(db_path: Path | None = None) -> None:
    """Initialize the database schema (backwards compatible import)."""
    _init_db(db_path=db_path)


__all__ = ["DB_PATH", "get_connection", "init_db", "test_connection"]

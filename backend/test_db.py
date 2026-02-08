"""Smoke test for verifying SQLite connectivity."""

from .db import test_connection


if __name__ == "__main__":
    test_connection()

"""Path helpers for repo resources and data storage."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def get_repo_root() -> Path:
    """Return the repository root directory."""
    return Path(__file__).resolve().parents[1]


def get_data_dir(app_name: str = "tu_app") -> Path:
    """Return the OS-appropriate data directory for the app."""
    if sys.platform.startswith("win"):
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~\\AppData\\Local")
        return Path(base) / app_name
    if sys.platform == "darwin":
        return Path(os.path.expanduser("~/Library/Application Support")) / app_name
    return get_repo_root() / "data"


def resolve_repo_path(*parts: str) -> Path:
    """Resolve a path relative to the repository root."""
    return get_repo_root().joinpath(*parts)


def resolve_asset_path(relative_path: str) -> Path:
    """Resolve an asset path relative to the repository root."""
    return resolve_repo_path(relative_path)

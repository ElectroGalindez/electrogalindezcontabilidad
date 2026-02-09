"""Helpers to backup and restore the local data folder."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.paths import resolve_repo_path


def backup_data_folder(dest_folder: Optional[str] = None) -> str:
    """
    Crear un backup completo de la carpeta `data` con timestamp.
    Si se pasa dest_folder, el backup se guarda allí.
    """
    base_dir = resolve_repo_path()
    data_dir = base_dir / "data"
    backups_dir = Path(dest_folder) if dest_folder else base_dir / "backups"
    backups_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backups_dir / f"backup_{timestamp}"

    if backup_path.exists():
        shutil.rmtree(backup_path)
    shutil.copytree(data_dir, backup_path)
    return str(backup_path)


def restore_backup(backup_folder: str) -> str:
    """Restaurar un backup sobre la carpeta `data`."""
    base_dir = resolve_repo_path()
    data_dir = base_dir / "data"
    backup_path = Path(backup_folder)

    if not backup_path.exists() or not backup_path.is_dir():
        raise FileNotFoundError(f"Backup no encontrado: {backup_folder}")

    if data_dir.exists():
        shutil.rmtree(data_dir)
    shutil.copytree(backup_path, data_dir)
    return str(data_dir)

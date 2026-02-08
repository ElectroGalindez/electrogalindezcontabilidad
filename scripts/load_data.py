"""Load CSV exports into the local SQLite database."""

from __future__ import annotations

import argparse
from pathlib import Path

from data.db import DB_PATH, init_db, is_db_empty, load_csvs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import CSVs into the local SQLite database.")
    parser.add_argument(
        "--csv-dir",
        type=Path,
        default=None,
        help="Directorio con CSVs exportados (por defecto data/csv).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Importa CSVs incluso si la base ya tiene datos.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    init_db()
    if not args.force and not is_db_empty():
        print("La base ya contiene datos. Usa --force para reimportar.")
        return

    results = load_csvs(csv_dir=args.csv_dir)
    if not results:
        print("No se encontraron CSVs para importar.")
        return

    print(f"Base de datos: {DB_PATH}")
    for result in results:
        print(f"{result.table}: {result.rows} filas importadas desde {result.path}")


if __name__ == "__main__":
    main()

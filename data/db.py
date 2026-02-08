"""SQLite data access layer with CSV bootstrap support."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping, Sequence
import sqlite3

import pandas as pd

from core.paths import get_data_dir, resolve_repo_path

APP_NAME = "tu_app"
DATA_DIR = get_data_dir(APP_NAME)
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_FILENAME = "local.db"
DB_PATH = DATA_DIR / DB_FILENAME
DEFAULT_CSV_DIR = resolve_repo_path("data", "csv")

TABLES: tuple[str, ...] = (
    "usuarios",
    "productos",
    "categorias",
    "clientes",
    "ventas",
    "deudas",
    "deudas_detalle",
    "logs",
    "auditoria",
    "notas",
)

SCHEMA: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        rol TEXT NOT NULL,
        activo INTEGER NOT NULL DEFAULT 1,
        intentos_fallidos INTEGER NOT NULL DEFAULT 0,
        bloqueado_hasta TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        requiere_cambio_password INTEGER NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        precio REAL NOT NULL,
        cantidad REAL NOT NULL,
        categoria_id INTEGER
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS categorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        telefono TEXT,
        ci TEXT,
        chapa TEXT,
        direccion TEXT,
        deuda_total REAL NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER,
        total REAL NOT NULL,
        pagado REAL NOT NULL,
        usuario TEXT,
        tipo_pago TEXT,
        fecha TEXT NOT NULL,
        productos_vendidos TEXT,
        observaciones TEXT,
        vendedor TEXT,
        telefono_vendedor TEXT,
        chofer TEXT,
        chapa TEXT,
        saldo REAL NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS deudas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER NOT NULL,
        venta_id INTEGER,
        monto_total REAL NOT NULL,
        estado TEXT NOT NULL,
        fecha TEXT NOT NULL,
        descripcion TEXT,
        productos TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS deudas_detalle (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        deuda_id INTEGER NOT NULL,
        producto_id INTEGER NOT NULL,
        cantidad REAL NOT NULL,
        precio_unitario REAL NOT NULL,
        estado TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT NOT NULL,
        accion TEXT NOT NULL,
        detalles TEXT,
        fecha TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS auditoria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        accion TEXT NOT NULL,
        producto_id INTEGER,
        usuario TEXT,
        fecha TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS notas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contenido TEXT NOT NULL,
        fecha TEXT NOT NULL
    )
    """,
)


@dataclass(frozen=True)
class CsvImportResult:
    table: str
    rows: int
    path: Path


def _connect(db_path: Path | None = None) -> sqlite3.Connection:
    """Create a SQLite connection with row access by name."""
    target = db_path or DB_PATH
    conn = sqlite3.connect(target)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Yield a managed SQLite connection with commit/rollback handling."""
    conn = _connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Path | None = None) -> None:
    """Create tables if they do not yet exist."""
    with _connect(db_path) as conn:
        for statement in SCHEMA:
            conn.execute(statement)
        conn.commit()


def is_db_empty(db_path: Path | None = None) -> bool:
    """Return True if all known tables are empty."""
    with _connect(db_path) as conn:
        for table in TABLES:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            if count and count[0] > 0:
                return False
    return True


def _normalize_table_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def load_csvs(
    csv_dir: Path | str | None = None,
    table_mapping: Mapping[str, str] | None = None,
    db_path: Path | None = None,
) -> list[CsvImportResult]:
    """Load CSV files into their matching tables.

    CSV files are matched to tables by file stem unless a mapping is provided.
    """
    resolved_dir = Path(csv_dir) if csv_dir else DEFAULT_CSV_DIR
    if not resolved_dir.exists():
        return []

    mapping = {k.lower(): v for k, v in (table_mapping or {}).items()}
    results: list[CsvImportResult] = []

    with _connect(db_path) as conn:
        for csv_path in sorted(resolved_dir.glob("*.csv")):
            stem = _normalize_table_name(csv_path.stem)
            table = mapping.get(stem, stem)
            if table not in TABLES:
                continue
            df = pd.read_csv(csv_path)
            if df.empty:
                continue
            df.to_sql(table, conn, if_exists="append", index=False)
            results.append(CsvImportResult(table=table, rows=len(df), path=csv_path))
        conn.commit()

    return results


def bootstrap_database(csv_dir: Path | str | None = None, db_path: Path | None = None) -> None:
    """Initialize schema and load CSVs when the database is empty."""
    init_db(db_path)
    if is_db_empty(db_path):
        load_csvs(csv_dir=csv_dir, db_path=db_path)


def fetch_all(sql: str, params: Sequence | None = None, db_path: Path | None = None) -> list[sqlite3.Row]:
    """Run a SELECT query and return all rows."""
    with _connect(db_path) as conn:
        cursor = conn.execute(sql, params or [])
        return cursor.fetchall()


def fetch_one(sql: str, params: Sequence | None = None, db_path: Path | None = None) -> sqlite3.Row | None:
    """Run a SELECT query and return a single row."""
    with _connect(db_path) as conn:
        cursor = conn.execute(sql, params or [])
        return cursor.fetchone()


def execute_sql(sql: str, params: Sequence | None = None, db_path: Path | None = None) -> int:
    """Execute a SQL statement and return the affected row count."""
    with get_connection(db_path) as conn:
        cursor = conn.execute(sql, params or [])
        return cursor.rowcount


def insert_row(table: str, data: Mapping[str, object], db_path: Path | None = None) -> int:
    """Insert a row and return the last row id."""
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    with get_connection(db_path) as conn:
        cursor = conn.execute(sql, list(data.values()))
        return int(cursor.lastrowid)


def update_rows(
    table: str,
    data: Mapping[str, object],
    where: str,
    params: Sequence | None = None,
    db_path: Path | None = None,
) -> int:
    """Update rows and return the affected row count."""
    assignments = ", ".join([f"{key} = ?" for key in data.keys()])
    sql = f"UPDATE {table} SET {assignments} WHERE {where}"
    values = list(data.values()) + list(params or [])
    return execute_sql(sql, values, db_path=db_path)


def delete_rows(table: str, where: str, params: Sequence | None = None, db_path: Path | None = None) -> int:
    """Delete rows and return the affected row count."""
    sql = f"DELETE FROM {table} WHERE {where}"
    return execute_sql(sql, params, db_path=db_path)


def test_connection(db_path: Path | None = None) -> None:
    """Check that the SQLite connection is working."""
    row = fetch_one("SELECT datetime('now')", db_path=db_path)
    timestamp = row[0] if row else datetime.now().isoformat()
    print("Conexión SQLite exitosa ✅", timestamp)


_BOOTSTRAPPED = False


def ensure_bootstrap(csv_dir: Path | str | None = None, db_path: Path | None = None) -> None:
    """Run one-time database bootstrap within the process."""
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return
    bootstrap_database(csv_dir=csv_dir, db_path=db_path)
    _BOOTSTRAPPED = True


if __name__ == "__main__":
    ensure_bootstrap()
    test_connection()

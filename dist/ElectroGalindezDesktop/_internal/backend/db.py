"""SQLite connection helpers and schema initialization."""

from contextlib import contextmanager
from datetime import datetime
import sqlite3

from core.paths import get_data_dir

APP_NAME = "tu_app"
DATA_DIR = get_data_dir(APP_NAME)
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "db.sqlite"


def _connect() -> sqlite3.Connection:
    """Create a SQLite connection with row access by name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_connection() -> sqlite3.Connection:
    """Yield a managed SQLite connection with commit/rollback handling."""
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create tables if they do not yet exist."""
    schema = [
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
    ]
    with _connect() as conn:
        for statement in schema:
            conn.execute(statement)
        conn.commit()


def test_connection() -> None:
    """Check that the SQLite connection is working."""
    with _connect() as conn:
        result = conn.execute("SELECT datetime('now')").fetchone()
        print("Conexión SQLite exitosa ✅", result[0] if result else datetime.now().isoformat())


init_db()

if __name__ == "__main__":
    test_connection()

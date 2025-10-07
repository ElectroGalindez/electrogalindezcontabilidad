# backend/logs.py
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy import text
from .db import engine  # Función que devuelve conexión SQLAlchemy

# ---------------------------
# Registrar un log
# ---------------------------

def registrar_log(usuario, accion, detalles=None):
    with engine.begin() as conn:  # usa begin() para transacción automática
        conn.execute(
            text(
                "INSERT INTO logs (usuario, accion, detalles, fecha) "
                "VALUES (:usuario, :accion, :detalles, :fecha)"
            ),
            {
                "usuario": usuario,
                "accion": accion,
                "detalles": str(detalles or {}),
                "fecha": datetime.now()
            }
        )

# ---------------------------
# Listar todos los logs
# ---------------------------
def listar_logs() -> List[Dict[str, Any]]:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM logs ORDER BY fecha DESC"))
        return [dict(row) for row in result.fetchall()]


def obtener_logs_usuario(username: str):
    """Devuelve los registros del historial de acciones de un usuario."""
    query = text("""
        SELECT usuario, accion, fecha, detalles
        FROM logs
        WHERE usuario = :usuario
        ORDER BY fecha DESC
        LIMIT 100
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"usuario": username})
        return [row._asdict() for row in result]
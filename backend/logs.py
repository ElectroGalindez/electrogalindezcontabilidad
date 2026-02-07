# backend/logs.py
from datetime import datetime
from typing import List, Dict, Any
from .db import get_connection

# ---------------------------
# Registrar un log
# ---------------------------

def registrar_log(usuario, accion, detalles=None):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO logs (usuario, accion, detalles, fecha) VALUES (?, ?, ?, ?)",
            (
                usuario,
                accion,
                str(detalles or {}),
                datetime.now().isoformat(),
            ),
        )

# ---------------------------
# Listar todos los logs
# ---------------------------
def listar_logs() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        result = conn.execute("SELECT * FROM logs ORDER BY fecha DESC")
        return [dict(row) for row in result.fetchall()]


def obtener_logs_usuario(username: str):
    """Devuelve los registros del historial de acciones de un usuario."""
    query = """
        SELECT usuario, accion, fecha, detalles
        FROM logs
        WHERE usuario = ?
        ORDER BY fecha DESC
        LIMIT 100
    """
    with get_connection() as conn:
        result = conn.execute(query, (username,))
        return [dict(row) for row in result.fetchall()]

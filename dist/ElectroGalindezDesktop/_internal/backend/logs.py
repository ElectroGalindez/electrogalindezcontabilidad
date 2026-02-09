"""Audit log helpers."""

from datetime import datetime
from typing import Any, Dict, List

from .db import get_connection


def registrar_log(usuario: str, accion: str, detalles: Any = None) -> None:
    """Registrar una acción en la tabla de logs."""
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


def listar_logs() -> List[Dict[str, Any]]:
    """Listar todos los logs registrados."""
    with get_connection() as conn:
        result = conn.execute("SELECT * FROM logs ORDER BY fecha DESC")
        return [dict(row) for row in result.fetchall()]


def obtener_logs_usuario(username: str) -> List[Dict[str, Any]]:
    """Devolver el historial de acciones de un usuario."""
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

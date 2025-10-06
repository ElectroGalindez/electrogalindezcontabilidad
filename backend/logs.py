# backend/logs.py
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy import text
from .db import get_connection  # Función que devuelve conexión SQLAlchemy

# ---------------------------
# Registrar un log
# ---------------------------
def registrar_log(usuario: str, accion: str, detalles: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Inserta un registro de log en la base de datos.
    """
    conn = get_connection()
    detalles = detalles or {}
    fecha = datetime.now()
    result = conn.execute(
        text("""
            INSERT INTO logs (usuario, accion, detalles, fecha)
            VALUES (:usuario, :accion, :detalles::jsonb, :fecha)
            RETURNING *
        """),
        {"usuario": usuario, "accion": accion, "detalles": json.dumps(detalles), "fecha": fecha}
    )
    conn.commit()
    return dict(result.fetchone())

# ---------------------------
# Listar todos los logs
# ---------------------------
def listar_logs() -> List[Dict[str, Any]]:
    conn = get_connection()
    result = conn.execute(text("SELECT * FROM logs ORDER BY fecha DESC"))
    return [dict(row) for row in result.fetchall()]

# ---------------------------
# Obtener logs de un usuario específico
# ---------------------------
def obtener_logs_usuario(username: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    result = conn.execute(
        text("SELECT * FROM logs WHERE usuario = :usuario ORDER BY fecha DESC"),
        {"usuario": username}
    )
    return [dict(row) for row in result.fetchall()]

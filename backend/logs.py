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

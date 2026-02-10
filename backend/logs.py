# backend/logs.py
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy import text
import json
from .db import engine  # Función que devuelve conexión SQLAlchemy

# ---------------------------
# Registrar un log
# ---------------------------

def registrar_log(usuario: str, accion: str, detalles: dict):
    """
    Registra una acción en la tabla de logs.
    Convierte los dict a JSON para que PostgreSQL pueda almacenarlo.
    """
    if isinstance(detalles, dict):
        detalles = json.dumps(detalles, default=str)  # default=str para datetime, Decimal, etc.

    if isinstance(usuario, dict):
        usuario = usuario.get("username", "sistema")  # o json.dumps(usuario) si quieres guardar todo

    fecha = datetime.now()
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO logs (usuario, accion, detalles, fecha) VALUES (:usuario, :accion, :detalles, :fecha)"),
            {"usuario": usuario, "accion": accion, "detalles": detalles, "fecha": fecha}
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
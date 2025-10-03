# backend/historial.py
"""
Funciones para obtener historial de cambios por registro (entidad+id) usando la base de datos Neon.
"""

from sqlalchemy import text
from .db import engine  # tu engine ya configurado para Neon


def historial_por_registro(entidad: str, id_registro: str):
    """
    Devuelve todos los logs relacionados con una entidad e id (ej: producto, cliente, venta, deuda).
    """
    with engine.connect() as conn:
        query = text("""
            SELECT *
            FROM logs
            WHERE detalles ->> :entidad_id_key = :id_registro
            ORDER BY fecha DESC
        """)
        result = conn.execute(
            query,
            {"entidad_id_key": f"{entidad}_id", "id_registro": id_registro}
        )
        logs = [dict(row) for row in result]

    return logs

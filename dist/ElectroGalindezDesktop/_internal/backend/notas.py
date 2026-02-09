"""Notes CRUD helpers."""

from datetime import datetime
from typing import Dict, List, Optional

from .db import get_connection


def list_notes() -> List[Dict]:
    """Listar todas las notas."""
    with get_connection() as conn:
        rows = conn.execute("SELECT id, contenido, fecha FROM notas ORDER BY fecha DESC").fetchall()
        return [dict(row) for row in rows]


def add_note(contenido: str) -> Dict:
    """Agregar una nota nueva."""
    contenido = (contenido or "").strip()
    if not contenido:
        raise ValueError("El contenido de la nota no puede estar vacío.")
    fecha = datetime.now().isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO notas (contenido, fecha) VALUES (:contenido, :fecha)",
            {"contenido": contenido, "fecha": fecha},
        )
        note_id = cursor.lastrowid
        row = conn.execute(
            "SELECT id, contenido, fecha FROM notas WHERE id = ?",
            (note_id,),
        ).fetchone()
        return dict(row)


def update_note(nota_id: int, contenido: str) -> Optional[Dict]:
    """Actualizar el contenido de una nota existente."""
    contenido = (contenido or "").strip()
    if not contenido:
        raise ValueError("El contenido de la nota no puede estar vacío.")
    with get_connection() as conn:
        conn.execute(
            "UPDATE notas SET contenido = :contenido WHERE id = :id",
            {"contenido": contenido, "id": nota_id},
        )
        row = conn.execute(
            "SELECT id, contenido, fecha FROM notas WHERE id = ?",
            (nota_id,),
        ).fetchone()
        return dict(row) if row else None


def delete_note(nota_id: int) -> bool:
    """Eliminar una nota por ID."""
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM notas WHERE id = ?", (nota_id,)).fetchone()
        if not row:
            return False
        conn.execute("DELETE FROM notas WHERE id = ?", (nota_id,))
        return True

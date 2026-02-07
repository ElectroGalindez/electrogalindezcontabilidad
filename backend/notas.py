from typing import List, Dict, Optional
from datetime import datetime
from .db import get_connection


def list_notes() -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT id, contenido, fecha FROM notas ORDER BY fecha DESC").fetchall()
        return [dict(row) for row in rows]


def add_note(contenido: str) -> Dict:
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
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM notas WHERE id = ?", (nota_id,)).fetchone()
        if not row:
            return False
        conn.execute("DELETE FROM notas WHERE id = ?", (nota_id,))
        return True

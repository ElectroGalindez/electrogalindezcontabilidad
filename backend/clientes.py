from typing import Dict, Any, Optional
from sqlalchemy import text
from .db import engine
from .logs import registrar_log

def get_client(cliente_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene un cliente por ID"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, nombre, telefono, ci, chapa, direccion, deuda_total FROM clientes WHERE id = :id"), {"id": cliente_id})
        row = result.first()
        return dict(row._mapping) if row else None

def add_client(nombre, telefono, ci, chapa, direccion):
    with engine.begin() as conn:
        query = text("""
            INSERT INTO clientes (nombre, telefono, ci, chapa, direccion)
            VALUES (:nombre, :telefono, :ci, :chapa, :direccion)
            RETURNING id, nombre
        """)
        result = conn.execute(query, {
            "nombre": nombre,
            "telefono": telefono,
            "ci": ci,
            "chapa": chapa,
            "direccion": direccion
        })
        row = result.fetchone()
        return row._mapping if row else None

def update_client(cliente_id: str, cambios: Dict[str, Any], usuario: str = "sistema") -> Dict[str, Any]:
    """Actualiza campos de un cliente existentes"""
    if not cambios:
        raise ValueError("No hay cambios para aplicar")
    sets = ", ".join([f"{k} = :{k}" for k in cambios])
    query = text(f"UPDATE clientes SET {sets} WHERE id = :id")
    try:
        with engine.begin() as conn:
            conn.execute(query, {**cambios, "id": cliente_id})
        registrar_log(usuario, "update_client", {"id": cliente_id, "cambios": cambios})
        return get_client(cliente_id)
    except Exception as e:
        registrar_log(usuario, "error_update_client", {"id": cliente_id, "error": str(e)})
        raise

def delete_client(cliente_id: str, usuario: str = "sistema") -> bool:
    """Elimina un cliente"""
    try:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM clientes WHERE id = :id"), {"id": cliente_id})
        registrar_log(usuario, "delete_client", {"id": cliente_id})
        return True
    except Exception as e:
        registrar_log(usuario, "error_delete_client", {"id": cliente_id, "error": str(e)})
        raise

def update_debt(cliente_id: str, monto: float, usuario: str = "sistema") -> Dict[str, Any]:
    """Actualiza la deuda del cliente de manera segura"""
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE clientes
                SET deuda_total = GREATEST(deuda_total + :monto, 0)
                WHERE id = :id
            """), {"id": cliente_id, "monto": monto})
        registrar_log(usuario, "update_debt", {"id": cliente_id, "monto": monto})
        return get_client(cliente_id)
    except Exception as e:
        registrar_log(usuario, "error_update_debt", {"id": cliente_id, "monto": monto, "error": str(e)})
        raise

def list_clients() -> list[Dict[str, Any]]:
    """Lista todos los clientes con campos esenciales"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, nombre, telefono, ci, chapa, direccion, deuda_total FROM clientes ORDER BY nombre"))
        return [dict(r._mapping) for r in result]

def edit_client(cliente_id: str, nombre: Optional[str] = None, telefono: Optional[str] = None,
                ci: Optional[str] = None, chapa: Optional[str] = None, direccion: Optional[str] = None,
                usuario: str = "sistema") -> Dict[str, Any]:
    """Edita un cliente existente"""
    cambios = {}
    if nombre is not None:
        cambios["nombre"] = nombre
    if telefono is not None:
        cambios["telefono"] = telefono
    if ci is not None:
        cambios["ci"] = ci
    if chapa is not None:
        cambios["chapa"] = chapa
    if direccion is not None:
        cambios["direccion"] = direccion
    return update_client(cliente_id, cambios, usuario)
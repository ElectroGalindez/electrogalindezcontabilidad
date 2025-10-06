# backend/clientes.py
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import text
from .db import engine
from .logs import registrar_log
from .db import engine
from .utils import generate_id
from .logs import registrar_log

# ---------------------------
# LISTAR Y OBTENER CLIENTES
# ---------------------------
def list_clients() -> List[Dict[str, Any]]:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM clientes ORDER BY nombre"))
        return [dict(r._mapping) for r in result]

def get_client(cliente_id: str) -> Optional[Dict[str, Any]]:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM clientes WHERE id = :id"), {"id": cliente_id})
        row = result.first()
        return dict(row._mapping) if row else None

# ---------------------------
# AGREGAR CLIENTE
# ---------------------------
def add_client(nombre, telefono, ci, chapa, direccion):
    with engine.begin() as conn:  # abre una transacción automáticamente
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
# ---------------------------
# EDITAR CLIENTE
# ---------------------------
def edit_client(cliente_id: str, cambios: Dict[str, Any], usuario=None) -> Dict[str, Any]:
    sets = ", ".join([f"{k} = :{k}" for k in cambios])
    query = text(f"UPDATE clientes SET {sets} WHERE id = :id")
    with engine.connect() as conn:
        conn.execute(query, {**cambios, "id": cliente_id})
        conn.commit()
    registrar_log(usuario or "sistema", "editar_cliente", {"cliente_id": cliente_id, "cambios": cambios})
    return get_client(cliente_id)

# ---------------------------
# ELIMINAR CLIENTE
# ---------------------------
def delete_client(cliente_id: str, usuario=None) -> bool:
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM clientes WHERE id = :id"), {"id": cliente_id})
        conn.commit()
    registrar_log(usuario or "sistema", "eliminar_cliente", {"cliente_id": cliente_id})
    return True

# ---------------------------
# ACTUALIZAR DEUDA
# ---------------------------
def update_debt(cliente_id: str, monto: float) -> Dict[str, Any]:
    with engine.connect() as conn:
        conn.execute(text("UPDATE clientes SET deuda_total = GREATEST(deuda_total + :monto, 0) WHERE id = :id"), {"id": cliente_id, "monto": monto})
        conn.commit()
    return get_client(cliente_id)

def update_client(client_id: str, nombre: str = None, telefono: str = None, ci: str = None, chapa: str = None, direccion: str = None, usuario: str = None):
    """Actualiza los datos de un cliente existente"""
    with engine.begin() as conn:
        # Obtener cliente actual
        cliente = get_client(client_id)
        if not cliente:
            raise ValueError(f"No existe el cliente con ID {client_id}")

        # Preparar nuevos valores
        nombre = nombre or cliente["nombre"]
        telefono = telefono or cliente.get("telefono", "")
        ci = ci or cliente.get("ci", "")
        chapa = chapa or cliente.get("chapa", "")
        direccion = direccion or cliente.get("direccion", "")

        query = text("""
            UPDATE clientes
            SET nombre = :nombre,
                telefono = :telefono,
                ci = :ci,
                chapa = :chapa,
                direccion = :direccion
            WHERE id = :id
        """)
        conn.execute(query, {
            "id": client_id,
            "nombre": nombre,
            "telefono": telefono,
            "ci": ci,
            "chapa": chapa,
            "direccion": direccion
        })

    registrar_log(usuario or "sistema", "update_client", {"id": client_id})
    return get_client(client_id)

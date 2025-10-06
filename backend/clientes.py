# backend/clientes.py
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from .db import get_connection
from .logs import registrar_log

# ---------------------------
# LISTAR Y OBTENER CLIENTES
# ---------------------------

def list_clients() -> List[Dict[str, Any]]:
    conn = get_connection()
    result = conn.execute(text("SELECT * FROM clientes ORDER BY nombre"))
    return [dict(row) for row in result.fetchall()]

def get_client(cliente_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    result = conn.execute(text("SELECT * FROM clientes WHERE id = :id"), {"id": cliente_id})
    row = result.fetchone()
    return dict(row) if row else None

# ---------------------------
# AGREGAR CLIENTE
# ---------------------------

def add_client(
    nombre: str,
    telefono: str = "",
    ci: str = "",
    chapa: str = "",
    direccion: str = "",
    usuario: str = None
) -> Dict[str, Any]:

    if not nombre.strip():
        raise ValueError("El nombre del cliente no puede estar vacío")

    conn = get_connection()
    # Comprobar si ya existe cliente con mismo CI o nombre
    result = conn.execute(text("SELECT * FROM clientes WHERE ci = :ci OR nombre = :nombre"), {"ci": ci, "nombre": nombre})
    if result.fetchone():
        raise ValueError(f"Cliente '{nombre}' ya existe")

    # Insertar cliente
    result = conn.execute(
        text("""
            INSERT INTO clientes (nombre, telefono, ci, chapa, direccion, deuda_total)
            VALUES (:nombre, :telefono, :ci, :chapa, :direccion, 0)
            RETURNING *
        """),
        {"nombre": nombre, "telefono": telefono, "ci": ci, "chapa": chapa, "direccion": direccion}
    )
    conn.commit()
    cliente = dict(result.fetchone())

    registrar_log(usuario or "sistema", "crear_cliente", cliente)
    return cliente

# ---------------------------
# EDITAR CLIENTE
# ---------------------------

def update_client(cliente_id: str, nuevos_datos: Dict[str, Any], usuario: str = None) -> Dict[str, Any]:
    conn = get_connection()
    cliente = get_client(cliente_id)
    if not cliente:
        raise KeyError(f"Cliente {cliente_id} no encontrado")

    # Actualizar solo campos permitidos
    campos = {k: v for k, v in nuevos_datos.items() if k in ["nombre", "telefono", "ci", "chapa", "direccion"]}
    if not campos:
        raise ValueError("No hay campos válidos para actualizar")

    set_clause = ", ".join([f"{k} = :{k}" for k in campos])
    campos["id"] = cliente_id
    conn.execute(text(f"UPDATE clientes SET {set_clause} WHERE id = :id"), campos)
    conn.commit()

    cliente_actualizado = get_client(cliente_id)
    registrar_log(usuario or "sistema", "editar_cliente", {"cliente_id": cliente_id, "cambios": campos})
    return cliente_actualizado

# ---------------------------
# ELIMINAR CLIENTE
# ---------------------------

def delete_client(cliente_id: str, usuario: str = None) -> bool:
    conn = get_connection()
    cliente = get_client(cliente_id)
    if not cliente:
        raise KeyError(f"Cliente {cliente_id} no encontrado")

    conn.execute(text("DELETE FROM clientes WHERE id = :id"), {"id": cliente_id})
    conn.commit()

    registrar_log(usuario or "sistema", "eliminar_cliente", {"cliente_id": cliente_id, "cliente": cliente})
    return True

# ---------------------------
# ACTUALIZAR DEUDA
# ---------------------------

def update_debt(cliente_id: str, monto: float) -> Dict[str, Any]:
    conn = get_connection()
    cliente = get_client(cliente_id)
    if not cliente:
        raise KeyError(f"Cliente {cliente_id} no encontrado")

    nueva_deuda = max(0, cliente.get("deuda_total", 0) + monto)
    conn.execute(text("UPDATE clientes SET deuda_total = :deuda WHERE id = :id"), {"deuda": nueva_deuda, "id": cliente_id})
    conn.commit()
    cliente_actualizado = get_client(cliente_id)
    return cliente_actualizado

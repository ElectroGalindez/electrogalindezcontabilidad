# backend/clientes.py
from backend.db import engine
from sqlalchemy import text
from .logs import registrar_log

# ---------------------------
# Listar todos los clientes
# ---------------------------
def list_clients():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM clientes ORDER BY nombre"))
        return [dict(r) for r in result]

# ---------------------------
# Obtener cliente por ID
# ---------------------------
def get_client(cliente_id):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM clientes WHERE id=:id"), {"id": cliente_id}).fetchone()
    return dict(result) if result else None

# ---------------------------
# Agregar cliente
# ---------------------------
def add_client(nombre, telefono="", ci="", chapa="", usuario=None):
    with engine.begin() as conn:
        result = conn.execute(
            text(
                "INSERT INTO clientes (nombre, telefono, ci, chapa, deuda_total) "
                "VALUES (:nombre, :telefono, :ci, :chapa, 0) RETURNING id"
            ),
            {"nombre": nombre, "telefono": telefono, "ci": ci, "chapa": chapa}
        )
        cliente_id = result.fetchone()[0]
    registrar_log(usuario or "sistema", "crear_cliente", {"cliente_id": cliente_id, "nombre": nombre})
    return get_client(cliente_id)

# ---------------------------
# Editar cliente
# ---------------------------
def edit_client(cliente_id, cambios, usuario=None):
    set_clause = ", ".join([f"{k}=:{k}" for k in cambios])
    cambios["id"] = cliente_id
    with engine.begin() as conn:
        conn.execute(text(f"UPDATE clientes SET {set_clause} WHERE id=:id"), cambios)
    registrar_log(usuario or "sistema", "editar_cliente", {"cliente_id": cliente_id, "cambios": cambios})
    return get_client(cliente_id)

# ---------------------------
# Actualizar deuda total
# ---------------------------
def update_debt(cliente_id, monto):
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE clientes SET deuda_total = GREATEST(deuda_total + :monto, 0) WHERE id=:id"),
            {"id": cliente_id, "monto": monto}
        )
    return get_client(cliente_id)

# ---------------------------
# Eliminar cliente
# ---------------------------
def delete_client(cliente_id, usuario=None):
    cliente = get_client(cliente_id)
    if not cliente:
        return None
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM clientes WHERE id=:id"), {"id": cliente_id})
    registrar_log(usuario or "sistema", "eliminar_cliente", {"cliente_id": cliente_id, "cliente": cliente})
    return cliente

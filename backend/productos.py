# backend/productos.py
from backend.db import engine
from sqlalchemy import text
from .logs import registrar_log

# =============================
# CRUD Productos en Neon
# =============================

def list_products():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM productos ORDER BY nombre"))
        productos = [dict(r) for r in result]
    return productos

def get_product(producto_id):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM productos WHERE id = :id"),
            {"id": producto_id}
        ).fetchone()
    return dict(result) if result else None

def agregar_producto(nombre, precio, cantidad, categoria, usuario=None):
    with engine.begin() as conn:
        result = conn.execute(
            text(
                "INSERT INTO productos (nombre, precio, cantidad, categoria) "
                "VALUES (:nombre, :precio, :cantidad, :categoria) RETURNING id"
            ),
            {"nombre": nombre, "precio": precio, "cantidad": cantidad, "categoria": categoria}
        )
        producto_id = result.fetchone()[0]
    registrar_log(usuario or "sistema", "crear_producto", {"producto_id": producto_id, "nombre": nombre})
    return get_product(producto_id)

def editar_producto(producto_id, nuevos_datos, usuario=None):
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE productos SET nombre=:nombre, precio=:precio, cantidad=:cantidad, categoria=:categoria "
                "WHERE id=:id"
            ),
            {"id": producto_id, **nuevos_datos}
        )
    registrar_log(usuario or "sistema", "editar_producto", {"producto_id": producto_id, "cambios": nuevos_datos})
    return get_product(producto_id)

def eliminar_producto(producto_id, usuario=None):
    prod = get_product(producto_id)
    if not prod:
        return None
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM productos WHERE id=:id"),
            {"id": producto_id}
        )
    registrar_log(usuario or "sistema", "eliminar_producto", {"producto_id": producto_id, "producto": prod})
    return prod

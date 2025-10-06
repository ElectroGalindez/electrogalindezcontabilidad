# backend/productos.py
from typing import List, Dict, Any
from sqlalchemy import text
from .db import engine
from .logs import registrar_log
from typing import Optional


# ---------------------------
# LISTAR PRODUCTOS
# ---------------------------
def list_products() -> List[Dict[str, Any]]:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM productos ORDER BY nombre"))
        return [dict(r._mapping) for r in result]

# ---------------------------
# AGREGAR PRODUCTO
# ---------------------------
def guardar_producto(
    nombre: str,
    precio: float,
    cantidad: int,
    categoria_id: str,
    usuario: Optional[str] = None
) -> dict:
    """
    Crea un nuevo producto o edita uno existente si ya existe.
    Devuelve el producto creado/actualizado como diccionario.
    """
    nombre = nombre.strip()
    if not nombre:
        raise ValueError("El nombre del producto no puede estar vacío.")

    with engine.begin() as conn:
        # Verificar si ya existe un producto con ese nombre
        select_query = text("SELECT * FROM productos WHERE nombre = :nombre")
        existing = conn.execute(select_query, {"nombre": nombre}).mappings().fetchone()

        if existing:
            # Editar producto existente
            update_query = text("""
                UPDATE productos
                SET precio = :precio,
                    cantidad = :cantidad,
                    categoria_id = :categoria_id
                WHERE id = :id
                RETURNING *
            """)
            updated = conn.execute(update_query, {
                "precio": precio,
                "cantidad": cantidad,
                "categoria_id": categoria_id,
                "id": existing["id"]
            }).mappings().fetchone()

            registrar_log(usuario or "sistema", "editar_producto", {
                "id": updated["id"],
                "nombre": nombre,
                "precio": precio,
                "cantidad": cantidad,
                "categoria_id": categoria_id
            })

            return dict(updated)

        else:
            # Crear nuevo producto
            insert_query = text("""
                INSERT INTO productos (nombre, precio, cantidad, categoria_id)
                VALUES (:nombre, :precio, :cantidad, :categoria_id)
                RETURNING *
            """)
            new_prod = conn.execute(insert_query, {
                "nombre": nombre,
                "precio": precio,
                "cantidad": cantidad,
                "categoria_id": categoria_id
            }).mappings().fetchone()

            registrar_log(usuario or "sistema", "crear_producto", {
                "id": new_prod["id"],
                "nombre": nombre,
                "precio": precio,
                "cantidad": cantidad,
                "categoria_id": categoria_id
            })

            return dict(new_prod)
# ---------------------------
# OBTENER PRODUCTO
# ---------------------------
def get_product(producto_id: str) -> Dict[str, Any]:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM productos WHERE id = :id"), {"id": producto_id})
        row = result.first()
        return dict(row._mapping) if row else None

# ---------------------------
# ELIMINAR PRODUCTO
# ---------------------------
def delete_product(producto_id: str, usuario=None) -> bool:
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM productos WHERE id = :id"), {"id": producto_id})
        conn.commit()
    
    registrar_log(usuario or "sistema", "eliminar_producto", {"id": producto_id})
    return True

# ---------------------------
#   adjust_stock
# ---------------------------

def adjust_stock(product_id: str, cantidad_delta: int, usuario=None) -> dict:
    """
    Ajusta el stock de un producto sumando o restando cantidad_delta.
    Devuelve el producto actualizado.
    """
    with engine.begin() as conn:
        # Obtener stock actual
        result = conn.execute(text("SELECT cantidad FROM productos WHERE id = :id"), {"id": product_id})
        prod = result.mappings().first()
        if not prod:
            raise ValueError(f"Producto {product_id} no encontrado")
        
        nuevo_stock = prod["cantidad"] + cantidad_delta
        if nuevo_stock < 0:
            raise ValueError(f"Stock insuficiente para {prod['nombre']}")
        
        conn.execute(
            text("UPDATE productos SET cantidad = :cantidad WHERE id = :id"),
            {"cantidad": nuevo_stock, "id": product_id}
        )
        
        # Opcional: registrar log
        if usuario:
            from .logs import registrar_log
            registrar_log(usuario, "ajustar_stock", {"producto_id": product_id, "delta": cantidad_delta})
        
        return {**prod, "cantidad": nuevo_stock}
    
def update_product(id_producto, nombre, cantidad, precio):
    query = text("""
        UPDATE productos
        SET nombre = :nombre, cantidad = :cantidad, precio = :precio
        WHERE id = :id
    """)
    with engine.begin() as conn:
        conn.execute(query, {"id": id_producto, "nombre": nombre, "cantidad": cantidad, "precio": precio})
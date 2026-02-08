# backend/productos.py
from typing import List, Dict, Any
from .db import get_connection
from .logs import registrar_log
from typing import Optional


# ---------------------------
# LISTAR PRODUCTOS
# ---------------------------
def list_products() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        result = conn.execute("SELECT * FROM productos ORDER BY nombre")
        return [dict(r) for r in result.fetchall()]

def map_productos() -> Dict[str, str]:
    with get_connection() as conn:
        result = conn.execute("SELECT id, nombre FROM productos")
        return {row["id"]: row["nombre"] for row in result.fetchall()}
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

    with get_connection() as conn:
        # Verificar si ya existe un producto con ese nombre
        select_query = "SELECT * FROM productos WHERE nombre = ?"
        existing = conn.execute(select_query, (nombre,)).fetchone()

        if existing:
            # Editar producto existente
            update_query = """
                UPDATE productos
                SET precio = :precio,
                    cantidad = :cantidad,
                    categoria_id = :categoria_id
                WHERE id = :id
            """
            conn.execute(update_query, {
                "precio": precio,
                "cantidad": cantidad,
                "categoria_id": categoria_id,
                "id": existing["id"],
            })
            updated = conn.execute("SELECT * FROM productos WHERE id = ?", (existing["id"],)).fetchone()

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
            insert_query = """
                INSERT INTO productos (nombre, precio, cantidad, categoria_id)
                VALUES (:nombre, :precio, :cantidad, :categoria_id)
            """
            cursor = conn.execute(insert_query, {
                "nombre": nombre,
                "precio": precio,
                "cantidad": cantidad,
                "categoria_id": categoria_id,
            })
            new_id = cursor.lastrowid
            new_prod = conn.execute("SELECT * FROM productos WHERE id = ?", (new_id,)).fetchone()

            registrar_log(usuario or "sistema", "crear_producto", {
                "id": new_prod["id"],
                "nombre": nombre,
                "precio": precio,
                "cantidad": cantidad,
                "categoria_id": categoria_id
            })

            return dict(new_prod)
        
# editar producto
def editar_producto(
    producto_id: str,
    nombre: str,
    precio: float,
    cantidad: int,
    categoria_id: str,
    usuario: Optional[str] = None
) -> dict:
    with get_connection() as conn:
        update_query = """
            UPDATE productos
            SET nombre = :nombre,
                precio = :precio,
                cantidad = :cantidad,
                categoria_id = :categoria_id
            WHERE id = :id
        """
        conn.execute(update_query, {
            "nombre": nombre,
            "precio": precio,
            "cantidad": cantidad,
            "categoria_id": categoria_id,
            "id": producto_id,
        })
        updated = conn.execute("SELECT * FROM productos WHERE id = ?", (producto_id,)).fetchone()

        registrar_log(usuario or "sistema", "editar_producto", {
            "id": updated["id"],
            "nombre": nombre,
            "precio": precio,
            "cantidad": cantidad,
            "categoria_id": categoria_id
        })

        return dict(updated)    
    



# ---------------------------
# OBTENER PRODUCTO
# ---------------------------
def get_product(producto_id: str) -> Dict[str, Any]:
    with get_connection() as conn:
        result = conn.execute("SELECT * FROM productos WHERE id = ?", (producto_id,))
        row = result.fetchone()
        return dict(row) if row else None

# ---------------------------
# ELIMINAR PRODUCTO
# ---------------------------
def delete_product(producto_id: str, usuario: Optional[str] = None) -> bool:
    with get_connection() as conn:
        # Obtener el nombre del producto antes de eliminarlo para el log
        result = conn.execute("SELECT nombre FROM productos WHERE id = ?", (producto_id,))
        row = result.fetchone()
        if not row:
            return False  # Producto no encontrado

        producto_nombre = row["nombre"]

        # Eliminar el producto
        conn.execute("DELETE FROM productos WHERE id = ?", (producto_id,))

        # Registrar log de eliminación
        if usuario:
            registrar_log(usuario, "eliminar_producto", {
                "id": producto_id,
                "nombre": producto_nombre
            })

        return True

# ---------------------------
#   adjust_stock
# ---------------------------

def adjust_stock(product_id: str, cantidad_delta: int, usuario=None) -> dict:
    """
    Ajusta el stock de un producto sumando o restando cantidad_delta.
    Devuelve el producto actualizado.
    """
    with get_connection() as conn:
        # Obtener stock actual
        result = conn.execute("SELECT cantidad FROM productos WHERE id = ?", (product_id,))
        prod = result.fetchone()
        if not prod:
            raise ValueError(f"Producto {product_id} no encontrado")
        
        nuevo_stock = prod["cantidad"] + cantidad_delta
        if nuevo_stock < 0:
            raise ValueError(f"Stock insuficiente para {prod['nombre']}")
        
        conn.execute(
            "UPDATE productos SET cantidad = ? WHERE id = ?",
            (nuevo_stock, product_id),
        )
        
        # Opcional: registrar log
        if usuario:
            from .logs import registrar_log
            registrar_log(usuario, "ajustar_stock", {"producto_id": product_id, "delta": cantidad_delta})
        
        return {**dict(prod), "cantidad": nuevo_stock}
    
def update_product(id_producto, nombre, cantidad, precio):
    query = """
        UPDATE productos
        SET nombre = :nombre, cantidad = :cantidad, precio = :precio
        WHERE id = :id
    """
    with get_connection() as conn:
        conn.execute(query, {"id": id_producto, "nombre": nombre, "cantidad": cantidad, "precio": precio})


def eliminar_producto(id_producto: int, usuario: str = None):
    """
    Elimina un producto de la base de datos por su ID y registra la acción en logs.
    """
    query = """
        DELETE FROM productos
        WHERE id = :id_producto
    """

    with get_connection() as conn:
        eliminado = conn.execute("SELECT id, nombre FROM productos WHERE id = ?", (id_producto,)).fetchone()
        if eliminado:
            conn.execute(query, {"id_producto": id_producto})

        if eliminado:
            # Registrar log si se proporciona usuario
            if usuario:
                registrar_log(usuario, f"Eliminó producto {eliminado['nombre']} (ID {eliminado['id']})")
            return dict(eliminado)  # Retornar como diccionario
        return None
        
        

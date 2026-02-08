"""Product management helpers."""

from typing import Any, Dict, List, Optional

from .db import get_connection
from .logs import registrar_log


def list_products() -> List[Dict[str, Any]]:
    """Listar todos los productos disponibles."""
    with get_connection() as conn:
        result = conn.execute("SELECT * FROM productos ORDER BY nombre")
        return [dict(r) for r in result.fetchall()]


def map_productos() -> Dict[str, str]:
    """Mapear IDs de productos a sus nombres."""
    with get_connection() as conn:
        result = conn.execute("SELECT id, nombre FROM productos")
        return {row["id"]: row["nombre"] for row in result.fetchall()}


def guardar_producto(
    nombre: str,
    precio: float,
    cantidad: int,
    categoria_id: str,
    usuario: Optional[str] = None,
) -> dict:
    """
    Crear un nuevo producto o editar uno existente si ya existe.
    Devuelve el producto creado/actualizado como diccionario.
    """
    nombre = nombre.strip()
    if not nombre:
        raise ValueError("El nombre del producto no puede estar vacío.")

    with get_connection() as conn:
        select_query = "SELECT * FROM productos WHERE nombre = ?"
        existing = conn.execute(select_query, (nombre,)).fetchone()

        if existing:
            update_query = """
                UPDATE productos
                SET precio = :precio,
                    cantidad = :cantidad,
                    categoria_id = :categoria_id
                WHERE id = :id
            """
            conn.execute(
                update_query,
                {
                    "precio": precio,
                    "cantidad": cantidad,
                    "categoria_id": categoria_id,
                    "id": existing["id"],
                },
            )
            updated = conn.execute("SELECT * FROM productos WHERE id = ?", (existing["id"],)).fetchone()

            registrar_log(
                usuario or "sistema",
                "editar_producto",
                {
                    "id": updated["id"],
                    "nombre": nombre,
                    "precio": precio,
                    "cantidad": cantidad,
                    "categoria_id": categoria_id,
                },
            )

            return dict(updated)

        insert_query = """
            INSERT INTO productos (nombre, precio, cantidad, categoria_id)
            VALUES (:nombre, :precio, :cantidad, :categoria_id)
        """
        cursor = conn.execute(
            insert_query,
            {
                "nombre": nombre,
                "precio": precio,
                "cantidad": cantidad,
                "categoria_id": categoria_id,
            },
        )
        new_id = cursor.lastrowid
        new_prod = conn.execute("SELECT * FROM productos WHERE id = ?", (new_id,)).fetchone()

        registrar_log(
            usuario or "sistema",
            "crear_producto",
            {
                "id": new_prod["id"],
                "nombre": nombre,
                "precio": precio,
                "cantidad": cantidad,
                "categoria_id": categoria_id,
            },
        )

        return dict(new_prod)


def editar_producto(
    producto_id: str,
    nombre: str,
    precio: float,
    cantidad: int,
    categoria_id: str,
    usuario: Optional[str] = None,
) -> dict:
    """Editar un producto existente."""
    with get_connection() as conn:
        update_query = """
            UPDATE productos
            SET nombre = :nombre,
                precio = :precio,
                cantidad = :cantidad,
                categoria_id = :categoria_id
            WHERE id = :id
        """
        conn.execute(
            update_query,
            {
                "nombre": nombre,
                "precio": precio,
                "cantidad": cantidad,
                "categoria_id": categoria_id,
                "id": producto_id,
            },
        )
        updated = conn.execute("SELECT * FROM productos WHERE id = ?", (producto_id,)).fetchone()

        registrar_log(
            usuario or "sistema",
            "editar_producto",
            {
                "id": updated["id"],
                "nombre": nombre,
                "precio": precio,
                "cantidad": cantidad,
                "categoria_id": categoria_id,
            },
        )

        return dict(updated)


def get_product(producto_id: str) -> Dict[str, Any]:
    """Obtener un producto por ID."""
    with get_connection() as conn:
        result = conn.execute("SELECT * FROM productos WHERE id = ?", (producto_id,))
        row = result.fetchone()
        return dict(row) if row else None


def delete_product(producto_id: str, usuario: Optional[str] = None) -> bool:
    """Eliminar un producto por ID."""
    with get_connection() as conn:
        result = conn.execute("SELECT nombre FROM productos WHERE id = ?", (producto_id,))
        row = result.fetchone()
        if not row:
            return False

        producto_nombre = row["nombre"]
        conn.execute("DELETE FROM productos WHERE id = ?", (producto_id,))

        if usuario:
            registrar_log(
                usuario,
                "eliminar_producto",
                {"id": producto_id, "nombre": producto_nombre},
            )

        return True


def adjust_stock(product_id: str, cantidad_delta: int, usuario: Optional[str] = None) -> dict:
    """
    Ajustar el stock de un producto sumando o restando cantidad_delta.
    Devuelve el producto actualizado.
    """
    with get_connection() as conn:
        result = conn.execute("SELECT cantidad, nombre FROM productos WHERE id = ?", (product_id,))
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

        if usuario:
            registrar_log(
                usuario,
                "ajustar_stock",
                {"producto_id": product_id, "delta": cantidad_delta},
            )

        return {**dict(prod), "cantidad": nuevo_stock}


def update_product(
    producto_id: str,
    nombre: str,
    cantidad: float,
    precio: float,
    categoria_id: Optional[str] = None,
    usuario: Optional[str] = None,
) -> dict:
    """Actualizar un producto con datos opcionales."""
    with get_connection() as conn:
        update_query = """
            UPDATE productos
            SET nombre = :nombre,
                precio = :precio,
                cantidad = :cantidad,
                categoria_id = COALESCE(:categoria_id, categoria_id)
            WHERE id = :id
        """
        conn.execute(
            update_query,
            {
                "nombre": nombre,
                "precio": precio,
                "cantidad": cantidad,
                "categoria_id": categoria_id,
                "id": producto_id,
            },
        )
        updated = conn.execute("SELECT * FROM productos WHERE id = ?", (producto_id,)).fetchone()

        if usuario:
            registrar_log(
                usuario,
                "editar_producto",
                {
                    "id": producto_id,
                    "nombre": nombre,
                    "precio": precio,
                    "cantidad": cantidad,
                    "categoria_id": categoria_id,
                },
            )

        return dict(updated)


def eliminar_producto(producto_id: str, usuario: Optional[str] = None) -> bool:
    """Compatibilidad: eliminar un producto por ID."""
    return delete_product(producto_id, usuario=usuario)

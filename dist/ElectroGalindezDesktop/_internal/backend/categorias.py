"""Category management helpers."""

from typing import Dict, List, Optional

from .db import get_connection
from .logs import registrar_log


def _normalize_nombre(nombre: str) -> str:
    """Normalizar el nombre de una categoría."""
    nombre = nombre.strip()
    if not nombre:
        raise ValueError("El nombre de la categoría no puede estar vacío.")
    return nombre

def list_categories() -> List[Dict]:
    """Listar todas las categorías disponibles."""
    query = "SELECT id, nombre FROM categorias ORDER BY nombre ASC"
    with get_connection() as conn:
        result = conn.execute(query)
        return [dict(row) for row in result.fetchall()]

def get_category(cat_id: int) -> Optional[Dict]:
    """Obtener una categoría específica por ID."""
    query = "SELECT id, nombre FROM categorias WHERE id = ?"
    with get_connection() as conn:
        result = conn.execute(query, (cat_id,)).fetchone()
        return dict(result) if result else None

def agregar_categoria(nombre: str, usuario: str = None) -> str:
    """Agregar una nueva categoría."""
    nombre = _normalize_nombre(nombre)

    # Verificar duplicado
    categorias = [c["nombre"].lower() for c in list_categories()]
    if nombre.lower() in categorias:
        raise ValueError(f"La categoría '{nombre}' ya existe.")

    query = "INSERT INTO categorias (nombre) VALUES (:nombre)"
    with get_connection() as conn:
        conn.execute(query, {"nombre": nombre})

    registrar_log(usuario or "sistema", "crear_categoria", {"nombre": nombre})
    return nombre

def editar_categoria(cat_id: int, nombre_nuevo: str, usuario: str = None) -> str:
    """Editar el nombre de una categoría existente."""
    nombre_nuevo = _normalize_nombre(nombre_nuevo)

    categoria = get_category(cat_id)
    if not categoria:
        raise ValueError(f"La categoría con ID {cat_id} no existe.")

    categorias = [c["nombre"].lower() for c in list_categories() if c["id"] != cat_id]
    if nombre_nuevo.lower() in categorias:
        raise ValueError(f"La categoría '{nombre_nuevo}' ya existe.")

    query = "UPDATE categorias SET nombre = :nombre_nuevo WHERE id = :cat_id"
    with get_connection() as conn:
        conn.execute(query, {"nombre_nuevo": nombre_nuevo, "cat_id": cat_id})

    registrar_log(usuario or "sistema", "editar_categoria", {
        "id": cat_id,
        "nombre_nuevo": nombre_nuevo
    })
    return nombre_nuevo

def eliminar_categoria(cat_id: int, usuario: str = None):
    """Eliminar una categoría por ID."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, nombre FROM categorias WHERE id = ?",
            (cat_id,),
        ).fetchone()
        if row:
            conn.execute("DELETE FROM categorias WHERE id = ?", (cat_id,))
    if row:
        registrar_log(usuario or "sistema", "eliminar_categoria", dict(row))
        return dict(row)
    else:
        raise ValueError("Categoría no encontrada")

def list_products_by_category(categoria_id: int) -> list[dict]:
    """Listar productos de una categoría específica."""
    query = "SELECT * FROM productos WHERE categoria_id = ? ORDER BY nombre"
    with get_connection() as conn:
        result = conn.execute(query, (categoria_id,))
        return [dict(row) for row in result.fetchall()]

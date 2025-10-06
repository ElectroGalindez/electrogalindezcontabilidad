# backend/categorias.py
from sqlalchemy import text
from .db import get_connection  # Función que devuelve un connection/session de SQLAlchemy
from .logs import registrar_log

# ---------------------------
# Funciones de categorías
# ---------------------------

def cargar_categorias() -> list[str]:
    """Devuelve todas las categorías desde la DB"""
    conn = get_connection()
    query = text("SELECT nombre FROM categorias ORDER BY nombre")
    result = conn.execute(query)
    return [row["nombre"] for row in result.fetchall()]

def agregar_categoria(nombre: str, usuario: str = None) -> str:
    """Agrega una nueva categoría"""
    nombre = nombre.strip()
    if not nombre:
        raise ValueError("El nombre de la categoría no puede estar vacío.")

    categorias = cargar_categorias()
    if nombre.lower() in [c.lower() for c in categorias]:
        raise ValueError(f"La categoría '{nombre}' ya existe.")

    conn = get_connection()
    query = text("INSERT INTO categorias (nombre) VALUES (:nombre)")
    conn.execute(query, {"nombre": nombre})
    conn.commit()

    # Registrar log
    registrar_log(usuario or "sistema", "crear_categoria", {"nombre": nombre})
    return nombre

def editar_categoria(nombre_actual: str, nombre_nuevo: str, usuario: str = None) -> str:
    """Edita el nombre de una categoría existente"""
    nombre_nuevo = nombre_nuevo.strip()
    if not nombre_nuevo:
        raise ValueError("El nombre de la categoría no puede estar vacío.")

    categorias = cargar_categorias()
    if nombre_actual not in categorias:
        raise ValueError(f"La categoría '{nombre_actual}' no existe.")

    if nombre_nuevo.lower() in [c.lower() for c in categorias if c != nombre_actual]:
        raise ValueError(f"La categoría '{nombre_nuevo}' ya existe.")

    conn = get_connection()
    query = text("UPDATE categorias SET nombre = :nombre_nuevo WHERE nombre = :nombre_actual")
    conn.execute(query, {"nombre_nuevo": nombre_nuevo, "nombre_actual": nombre_actual})
    conn.commit()

    registrar_log(usuario or "sistema", "editar_categoria", {
        "nombre_actual": nombre_actual,
        "nombre_nuevo": nombre_nuevo
    })
    return nombre_nuevo

def eliminar_categoria(nombre: str, usuario: str = None) -> str:
    """Elimina una categoría"""
    categorias = cargar_categorias()
    if nombre not in categorias:
        raise ValueError(f"La categoría '{nombre}' no existe.")

    conn = get_connection()
    query = text("DELETE FROM categorias WHERE nombre = :nombre")
    conn.execute(query, {"nombre": nombre})
    conn.commit()

    registrar_log(usuario or "sistema", "eliminar_categoria", {"nombre": nombre})
    return nombre
def list_categories() -> list[dict]:
    """Devuelve todas las categorías como lista de dicts con id y nombre"""
    conn = get_connection()
    query = text("SELECT id, nombre FROM categorias ORDER BY nombre")
    result = conn.execute(query)
    return [{"id": row["id"], "nombre": row["nombre"]} for row in result.fetchall()]    
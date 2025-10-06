# backend/categorias.py
from sqlalchemy import text
from .db import engine
from .logs import registrar_log

# ---------------------------
# Funciones de categorías
# ---------------------------

def list_categories() -> list[dict]:
    """Devuelve todas las categorías con su id desde la DB"""
    query = text("SELECT id, nombre FROM categorias ORDER BY nombre ASC")
    with engine.connect() as conn:
        result = conn.execute(query)
        return [row for row in result.mappings().all()]  
    
def agregar_categoria(nombre: str, usuario: str = None) -> str:
    """Agrega una nueva categoría"""
    nombre = nombre.strip()
    if not nombre:
        raise ValueError("El nombre de la categoría no puede estar vacío.")

    # Verificar duplicado
    categorias = list_categories()
    if nombre.lower() in [c.lower() for c in categorias]:
        raise ValueError(f"La categoría '{nombre}' ya existe.")

    query = text("INSERT INTO categorias (nombre) VALUES (:nombre)")
    with engine.begin() as conn:  # begin() asegura commit automático
        conn.execute(query, {"nombre": nombre})

    registrar_log(usuario or "sistema", "crear_categoria", {"nombre": nombre})
    return nombre

def editar_categoria(nombre_actual: str, nombre_nuevo: str, usuario: str = None) -> str:
    """Edita el nombre de una categoría existente"""
    nombre_actual = nombre_actual.strip()
    nombre_nuevo = nombre_nuevo.strip()
    if not nombre_nuevo:
        raise ValueError("El nombre de la categoría no puede estar vacío.")

    categorias = list_categories()
    if nombre_actual not in categorias:
        raise ValueError(f"La categoría '{nombre_actual}' no existe.")
    if nombre_nuevo.lower() in [c.lower() for c in categorias if c != nombre_actual]:
        raise ValueError(f"La categoría '{nombre_nuevo}' ya existe.")

    query = text(
        "UPDATE categorias SET nombre = :nombre_nuevo WHERE nombre = :nombre_actual"
    )
    with engine.begin() as conn:
        conn.execute(query, {"nombre_nuevo": nombre_nuevo, "nombre_actual": nombre_actual})

    registrar_log(usuario or "sistema", "editar_categoria", {
        "nombre_actual": nombre_actual,
        "nombre_nuevo": nombre_nuevo
    })
    return nombre_nuevo

def eliminar_categoria(nombre: str, usuario: str = None) -> str:
    """Elimina una categoría"""
    nombre = nombre.strip()
    categorias = list_categories()
    if nombre not in categorias:
        raise ValueError(f"La categoría '{nombre}' no existe.")

    query = text("DELETE FROM categorias WHERE nombre = :nombre")
    with engine.begin() as conn:
        conn.execute(query, {"nombre": nombre})

    registrar_log(usuario or "sistema", "eliminar_categoria", {"nombre": nombre})
    return nombre

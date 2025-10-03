# backend/categorias.py
from sqlalchemy import text
from backend.db import engine
from .logs import registrar_log

def cargar_categorias():
    """Devuelve lista de nombres de todas las categorías"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT nombre FROM categorias ORDER BY nombre"))
        return [r["nombre"] for r in result]

def agregar_categoria(nombre, usuario=None):
    nombre = nombre.strip()
    if not nombre:
        raise ValueError("El nombre de la categoría no puede estar vacío.")

    existentes = cargar_categorias()
    if nombre.lower() in [c.lower() for c in existentes]:
        raise ValueError(f"La categoría '{nombre}' ya existe.")

    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO categorias (nombre) VALUES (:nombre)"),
            {"nombre": nombre}
        )
    registrar_log(usuario or "sistema", "crear_categoria", {"nombre": nombre})
    return nombre

def editar_categoria(nombre_actual, nombre_nuevo, usuario=None):
    nombre_actual = nombre_actual.strip()
    nombre_nuevo = nombre_nuevo.strip()
    if not nombre_nuevo:
        raise ValueError("El nombre de la categoría no puede estar vacío.")

    existentes = cargar_categorias()
    if nombre_actual not in existentes:
        raise ValueError(f"La categoría '{nombre_actual}' no existe.")
    if nombre_nuevo.lower() in [c.lower() for c in existentes if c != nombre_actual]:
        raise ValueError(f"La categoría '{nombre_nuevo}' ya existe.")

    with engine.begin() as conn:
        conn.execute(
            text("UPDATE categorias SET nombre=:nuevo WHERE nombre=:actual"),
            {"nuevo": nombre_nuevo, "actual": nombre_actual}
        )
    registrar_log(usuario or "sistema", "editar_categoria", {"nombre_actual": nombre_actual, "nombre_nuevo": nombre_nuevo})
    return nombre_nuevo

def eliminar_categoria(nombre, usuario=None):
    nombre = nombre.strip()
    existentes = cargar_categorias()
    if nombre not in existentes:
        raise ValueError(f"La categoría '{nombre}' no existe.")

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM categorias WHERE nombre=:nombre"), {"nombre": nombre})

    registrar_log(usuario or "sistema", "eliminar_categoria", {"nombre": nombre})
    return nombre

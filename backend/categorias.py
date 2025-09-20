import os
import json

CATEGORIAS_FILE = os.path.join(os.path.dirname(__file__), "../data/categorias.json")

def cargar_categorias():
    if not os.path.exists(CATEGORIAS_FILE):
        return []
    with open(CATEGORIAS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def guardar_categorias(categorias):
    with open(CATEGORIAS_FILE, "w", encoding="utf-8") as f:
        json.dump(categorias, f, indent=4, ensure_ascii=False)

def agregar_categoria(nombre):
    nombre = nombre.strip()
    if not nombre:
        raise ValueError("El nombre de la categoría no puede estar vacío.")
    categorias = cargar_categorias()
    if nombre.lower() in [c.lower() for c in categorias]:
        raise ValueError(f"La categoría '{nombre}' ya existe.")
    categorias.append(nombre)
    guardar_categorias(categorias)
    return nombre

def editar_categoria(nombre_actual, nombre_nuevo):
    nombre_nuevo = nombre_nuevo.strip()
    if not nombre_nuevo:
        raise ValueError("El nombre de la categoría no puede estar vacío.")
    categorias = cargar_categorias()
    if nombre_actual not in categorias:
        raise ValueError(f"La categoría '{nombre_actual}' no existe.")
    if nombre_nuevo.lower() in [c.lower() for c in categorias if c != nombre_actual]:
        raise ValueError(f"La categoría '{nombre_nuevo}' ya existe.")
    idx = categorias.index(nombre_actual)
    categorias[idx] = nombre_nuevo
    guardar_categorias(categorias)
    return nombre_nuevo

def eliminar_categoria(nombre):
    categorias = cargar_categorias()
    if nombre not in categorias:
        raise ValueError(f"La categoría '{nombre}' no existe.")
    categorias = [c for c in categorias if c != nombre]
    guardar_categorias(categorias)
    return nombre

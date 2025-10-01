
from .utils import read_json, write_json_atomic

FILENAME = "categorias.json"


def cargar_categorias():
    return read_json(FILENAME)


def guardar_categorias(categorias):
    write_json_atomic(FILENAME, categorias)

def agregar_categoria(nombre, usuario=None):
    nombre = nombre.strip()
    if not nombre:
        raise ValueError("El nombre de la categoría no puede estar vacío.")
    categorias = cargar_categorias()
    if nombre.lower() in [c.lower() for c in categorias]:
        raise ValueError(f"La categoría '{nombre}' ya existe.")
    categorias.append(nombre)
    guardar_categorias(categorias)
    # Registrar log de creación de categoría
    try:
        from .logs import registrar_log
        registrar_log(usuario or "sistema", "crear_categoria", {
            "nombre": nombre
        })
    except Exception:
        pass
    return nombre

def editar_categoria(nombre_actual, nombre_nuevo, usuario=None):
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
    # Registrar log de edición de categoría
    try:
        from .logs import registrar_log
        registrar_log(usuario or "sistema", "editar_categoria", {
            "nombre_actual": nombre_actual,
            "nombre_nuevo": nombre_nuevo
        })
    except Exception:
        pass
    return nombre_nuevo

def eliminar_categoria(nombre, usuario=None):
    categorias = cargar_categorias()
    if nombre not in categorias:
        raise ValueError(f"La categoría '{nombre}' no existe.")
    categorias = [c for c in categorias if c != nombre]
    guardar_categorias(categorias)
    # Registrar log de eliminación de categoría
    try:
        from .logs import registrar_log
        registrar_log(usuario or "sistema", "eliminar_categoria", {
            "nombre": nombre
        })
    except Exception:
        pass
    return nombre

import os
import json
import random
import string

PRODUCTOS_FILE = os.path.join(os.path.dirname(__file__), "../data/productos.json")

# =============================
# Función interna para generar ID
# =============================
def _generar_id():
    return "P" + "".join(random.choices(string.ascii_uppercase + string.digits, k=5))

# =============================
# Cargar y guardar productos
# =============================
def cargar_productos():
    if not os.path.exists(PRODUCTOS_FILE):
        return []
    with open(PRODUCTOS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def guardar_productos(productos):
    with open(PRODUCTOS_FILE, "w", encoding="utf-8") as f:
        json.dump(productos, f, indent=4, ensure_ascii=False)

# =============================
# Validaciones
# =============================
def _validar_producto(nombre, precio, cantidad, categoria, ignorar_id=None):
    if not nombre.strip():
        raise ValueError("El nombre del producto no puede estar vacío.")
    if precio <= 0:
        raise ValueError("El precio debe ser mayor que 0.")
    if cantidad < 0:
        raise ValueError("La cantidad no puede ser negativa.")
    if not categoria.strip():
        raise ValueError("La categoría no puede estar vacía.")
    productos = cargar_productos()
    for p in productos:
        if p["nombre"].lower() == nombre.lower() and p["id"] != ignorar_id:
            raise ValueError(f"Ya existe un producto con el nombre '{nombre}'.")

# =============================
# Funciones CRUD
# =============================
def agregar_producto(nombre, precio, cantidad, categoria):
    _validar_producto(nombre, precio, cantidad, categoria)
    productos = cargar_productos()
    nuevo = {
        "id": _generar_id(),
        "nombre": nombre.strip(),
        "precio": round(float(precio), 2),
        "cantidad": int(cantidad),
        "categoria": categoria.strip()
    }
    productos.append(nuevo)
    guardar_productos(productos)
    return nuevo

def editar_producto(producto_id, nuevos_datos):
    _validar_producto(
        nuevos_datos["nombre"],
        nuevos_datos["precio"],
        nuevos_datos["cantidad"],
        nuevos_datos["categoria"],
        ignorar_id=producto_id
    )
    productos = cargar_productos()
    for p in productos:
        if p["id"] == producto_id:
            p.update({
                "nombre": nuevos_datos["nombre"],
                "precio": round(float(nuevos_datos["precio"]), 2),
                "cantidad": int(nuevos_datos["cantidad"]),
                "categoria": nuevos_datos["categoria"]
            })
            break
    guardar_productos(productos)

def eliminar_producto(producto_id):
    productos = cargar_productos()
    productos = [p for p in productos if p["id"] != producto_id]
    guardar_productos(productos)

# =============================
# Funciones de consulta
# =============================
def get_product(producto_id):
    """
    Devuelve el producto completo según su ID.
    Retorna None si no existe.
    """
    productos = cargar_productos()
    return next((p for p in productos if p["id"] == producto_id), None)

def list_products():
    """
    Devuelve la lista completa de productos.
    """
    return cargar_productos()

def adjust_stock(producto_id, cantidad_cambio):
    """
    Ajusta el stock de un producto según la cantidad_cambio.
    Puede ser positivo (sumar) o negativo (restar).
    Lanza ValueError si el stock final sería negativo.
    """
    productos = cargar_productos()
    producto = next((p for p in productos if p["id"] == producto_id), None)
    if not producto:
        raise ValueError(f"Producto con ID '{producto_id}' no encontrado.")
    nuevo_stock = producto["cantidad"] + cantidad_cambio
    if nuevo_stock < 0:
        raise ValueError(f"No hay suficiente stock para '{producto['nombre']}'")
    producto["cantidad"] = nuevo_stock
    guardar_productos(productos)
    return producto

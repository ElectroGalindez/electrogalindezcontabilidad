
from .utils import read_json, write_json_atomic, generate_id, validate_product

FILENAME = "productos.json"

# =============================
# Función interna para generar ID
# =============================


# =============================
# Cargar y guardar productos
# =============================

def cargar_productos():
    return read_json(FILENAME)


def guardar_productos(productos):
    write_json_atomic(FILENAME, productos)

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
        "id": generate_id("P", productos),
        "nombre": nombre.strip(),
        "precio": round(float(precio), 2),
        "cantidad": int(cantidad),
        "categoria": categoria.strip()
    }
    if not validate_product(nuevo):
        raise ValueError("Estructura de producto inválida")
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
            if not validate_product(p):
                raise ValueError("Estructura de producto inválida tras edición")
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
    productos = cargar_productos()
    return next((p for p in productos if p["id"] == producto_id), None)


def list_products():
    return cargar_productos()


def adjust_stock(producto_id, cantidad_cambio):
    productos = cargar_productos()
    producto = next((p for p in productos if p["id"] == producto_id), None)
    if not producto:
        raise ValueError(f"Producto con ID '{producto_id}' no encontrado.")
    nuevo_stock = producto["cantidad"] + cantidad_cambio
    if nuevo_stock < 0:
        raise ValueError(f"No hay suficiente stock para '{producto['nombre']}'")
    producto["cantidad"] = nuevo_stock
    if not validate_product(producto):
        raise ValueError("Estructura de producto inválida tras ajuste de stock")
    guardar_productos(productos)
    return producto

# backend/ventas.py
from typing import  Dict, Optional
from datetime import datetime
from sqlalchemy import text
from backend.db import engine
from .productos import  get_product, update_product
from .logs import registrar_log
import json

# ----------------------------
# Funciones de ventas
# ----------------------------

# =========================
# Registrar una venta
# =========================
def register_sale(cliente_id, items, pagado, tipo_pago, usuario=None):
    """
    Registra una venta en la base de datos, actualiza stock y guarda productos vendidos.
    
    items: lista de dicts [{"id_producto": int, "nombre": str, "cantidad": int, "precio_unitario": float}]
    """
    if not items:
        raise ValueError("No hay productos para registrar en la venta.")

    # Calcular total
    total = sum(item["cantidad"] * item["precio_unitario"] for item in items)

    # Guardar productos vendidos como JSON
    productos_vendidos_json = json.dumps(items)

    fecha = datetime.now()

    # Query para insertar venta
    query = text("""
        INSERT INTO ventas (fecha, cliente_id, total, pagado, tipo_pago, productos_vendidos)
        VALUES (:fecha, :cliente_id, :total, :pagado, :tipo_pago, :productos_vendidos)
        RETURNING id, total
    """)

    with engine.begin() as conn:
        result = conn.execute(query, {
            "fecha": fecha,
            "cliente_id": cliente_id,
            "total": total,
            "pagado": pagado,
            "tipo_pago": tipo_pago,
            "productos_vendidos": productos_vendidos_json
        })
        venta_registrada = result.mappings().fetchone()

        # Actualizar stock de productos
        for item in items:
            prod = get_product(item["id_producto"])
            if prod is None:
                raise ValueError(f"Producto con ID {item['id_producto']} no encontrado.")
            nuevo_stock = prod["cantidad"] - item["cantidad"]
            if nuevo_stock < 0:
                raise ValueError(f"Stock insuficiente para {prod['nombre']}")
            update_product(
                id_producto=item["id_producto"],
                nombre=prod["nombre"],
                cantidad=nuevo_stock,
                precio=prod["precio"]
            )

    return dict(venta_registrada)


# =========================
# Listar ventas
# =========================
def list_sales():
    """
    Devuelve todas las ventas de la base de datos con productos_vendidos como lista de dicts.
    """
    query = text("SELECT * FROM ventas ORDER BY fecha DESC")
    with engine.connect() as conn:
        resultados = conn.execute(query).mappings().all()

    ventas_list = []
    for r_dict in resultados:
        # Decodificar JSON de productos vendidos
        productos_vendidos = r_dict["productos_vendidos"]
        if isinstance(productos_vendidos, str):
            try:
                productos_vendidos = json.loads(productos_vendidos)
            except json.JSONDecodeError:
                productos_vendidos = []
        r_dict = dict(r_dict)
        r_dict["productos_vendidos"] = productos_vendidos
        ventas_list.append(r_dict)

    return ventas_list

def get_sale(sale_id: str) -> Optional[Dict]:
    """Devuelve una venta por su ID"""
    query = text("SELECT * FROM ventas WHERE id = :id")
    with engine.connect() as conn:
        result = conn.execute(query, {"id": sale_id}).mappings().first()
    if result:
        r = dict(result)
        r["productos_vendidos"] = json.loads(r["productos_vendidos"])
        return r
    return None



def delete_sale(sale_id: str, usuario: Optional[str] = None) -> bool:
    """Elimina una venta por su ID"""
    sale = get_sale(sale_id)
    if not sale:
        return False

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM ventas WHERE id = :id"), {"id": sale_id})

    registrar_log(usuario or "sistema", "eliminar_venta", {"venta_id": sale_id, "venta": sale})
    return True

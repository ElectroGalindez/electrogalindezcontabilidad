# backend/ventas.py
from typing import  Dict, Optional
from datetime import datetime
from sqlalchemy import text
from backend.db import engine
from .productos import  get_product, update_product
from .logs import registrar_log
from .deudas import add_debt
import json

# ------------------------------
# Registrar venta
# ----------------------------
def register_sale(cliente_id, total, pagado, usuario, tipo_pago, productos=None):
    """
    Registra una venta y descuenta del inventario correctamente.
    """
    fecha = datetime.now()
    with engine.begin() as conn:
        # Guardar venta
        query_venta = text("""
            INSERT INTO ventas (cliente_id, total, pagado, usuario, tipo_pago, fecha)
            VALUES (:cliente_id, :total, :pagado, :usuario, :tipo_pago, :fecha)
            RETURNING id
        """)
        venta_id = conn.execute(query_venta, {
            "cliente_id": cliente_id,
            "total": total,
            "pagado": pagado,
            "usuario": usuario,
            "tipo_pago": tipo_pago,
            "fecha": fecha
        }).scalar()

        # Guardar detalle de productos y actualizar inventario
        if productos:
            for item in productos:
                prod_id = item.get("id_producto") or item.get("id")
                cantidad_vendida = float(item.get("cantidad", 0))
                precio_unitario = float(item.get("precio_unitario", 0.0))

                # Insertar detalle
                conn.execute(text("""
                    INSERT INTO ventas_detalle (venta_id, producto_id, cantidad, precio_unitario)
                    VALUES (:venta_id, :producto_id, :cantidad, :precio_unitario)
                """), {
                    "venta_id": venta_id,
                    "producto_id": prod_id,
                    "cantidad": cantidad_vendida,
                    "precio_unitario": precio_unitario
                })

                # Actualizar stock
                producto = get_product(prod_id)
                if producto:
                    stock_actual = float(producto.get("cantidad", 0))
                    nuevo_stock = max(stock_actual - cantidad_vendida, 0)
                    update_product(prod_id, nombre=producto["nombre"], cantidad=nuevo_stock, precio=producto["precio"])

        registrar_log(usuario, "registrar_venta", {"venta_id": venta_id, "total": total, "pagado": pagado})

    return {"id": venta_id, "total": total, "pagado": pagado, "fecha": fecha, "productos_vendidos": productos or []}

# ----------------------------
# Listar ventas
# ----------------------------
def list_sales():
    """
    Devuelve todas las ventas de la base de datos con productos_vendidos como lista de dicts.
    """
    query = text("SELECT * FROM ventas ORDER BY fecha DESC")
    with engine.connect() as conn:
        resultados = conn.execute(query).mappings().all()

    ventas_list = []
    for r_dict in resultados:
        productos_vendidos = r_dict.get("productos_vendidos") or "[]"
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

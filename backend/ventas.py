# backend/ventas.py
from typing import  Dict, Optional
from datetime import datetime
from sqlalchemy import text
from backend.db import engine
from .productos import  get_product, update_product
from .logs import registrar_log
from .deudas import add_debt
import json

# ----------------------------
# Funciones de ventas
# ----------------------------


def register_sale(cliente_id, total, pagado, usuario, tipo_pago, productos=None):
    """
    Registra una venta en la base de datos, opcionalmente con los productos.
    """
    # Guardar venta
    query = text("""
        INSERT INTO ventas (cliente_id, total, pagado, usuario, tipo_pago, fecha)
        VALUES (:cliente_id, :total, :pagado, :usuario, :tipo_pago, :fecha)
        RETURNING id
    """)
    fecha = datetime.now()
    with engine.begin() as conn:
        result = conn.execute(query, {
            "cliente_id": cliente_id,
            "total": total,
            "pagado": pagado,
            "usuario": usuario,
            "tipo_pago": tipo_pago,
            "fecha": fecha
        })
        venta_id = result.scalar()
        
        # Guardar productos si se pasó la lista
        if productos:
            for item in productos:
                conn.execute(text("""
                    INSERT INTO ventas_detalle (venta_id, producto_id, cantidad, precio_unitario)
                    VALUES (:venta_id, :producto_id, :cantidad, :precio_unitario)
                """), {
                    "venta_id": venta_id,
                    "producto_id": item.get("id_producto"),
                    "cantidad": item.get("cantidad"),
                    "precio_unitario": item.get("precio_unitario")
                })
    return {"id": venta_id, "total": total}

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

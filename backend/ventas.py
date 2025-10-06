# backend/ventas.py
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy import text
from backend.db import engine
from .productos import adjust_stock
from .deudas import update_debt
from .clientes import get_client
from .logs import registrar_log
import json

# ----------------------------
# Funciones de ventas
# ----------------------------

def list_sales() -> List[Dict]:
    """Devuelve todas las ventas como lista de diccionarios"""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, fecha, cliente_id, total, pagado, tipo_pago, productos_vendidos
            FROM ventas
            ORDER BY fecha DESC
        """)).mappings().all()
    ventas = []
    for r in result:
        r_dict = dict(r)
        # Convertir productos_vendidos de JSON string a lista
        r_dict["productos_vendidos"] = json.loads(r_dict["productos_vendidos"])
        ventas.append(r_dict)
    return ventas

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


def register_sale(cliente_id, items, pagado, tipo_pago, usuario):
    """
    Registra una venta en la base de datos.

    Parámetros:
        cliente_id (int): ID del cliente.
        items (list): Lista de diccionarios con los productos de la venta.
        pagado (float): Monto pagado.
        tipo_pago (str): Método de pago.
        usuario (str): Usuario que registra la venta.

    Retorna:
        dict: {'id': id_venta, 'total': total_venta}
    """
    if not items:
        raise ValueError("No se puede registrar una venta sin productos.")

    total = sum(item["cantidad"] * item["precio_unitario"] for item in items)
    productos_json = json.dumps(items)

    query = text("""
        INSERT INTO ventas (fecha, cliente_id, total, pagado, tipo_pago, productos_vendidos, usuario)
        VALUES (:fecha, :cliente_id, :total, :pagado, :tipo_pago, :productos_vendidos, :usuario)
        RETURNING id, total
    """)

    with engine.begin() as conn:
        result = conn.execute(query, {
            "fecha": datetime.now(),
            "cliente_id": cliente_id,
            "total": total,
            "pagado": pagado,
            "tipo_pago": tipo_pago,
            "productos_vendidos": productos_json,
            "usuario": usuario
        })
        venta = result.fetchone()

    return {"id": venta.id, "total": float(venta.total)}

def delete_sale(sale_id: str, usuario: Optional[str] = None) -> bool:
    """Elimina una venta por su ID"""
    sale = get_sale(sale_id)
    if not sale:
        return False

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM ventas WHERE id = :id"), {"id": sale_id})

    registrar_log(usuario or "sistema", "eliminar_venta", {"venta_id": sale_id, "venta": sale})
    return True

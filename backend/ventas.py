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


def register_sale(cliente_id, productos, total, pagado, tipo_pago=None, usuario=None):
    """
    Registra una venta. Si hay saldo pendiente, crea automáticamente una deuda
    después de confirmar la venta (para respetar la clave foránea).
    """
    if not productos:
        raise ValueError("No hay productos para registrar en la venta.")

    fecha = datetime.now()

    # 1️⃣ Guardar la venta primero (y confirmar)
    insert_venta = text("""
        INSERT INTO ventas (fecha, cliente_id, total, pagado, tipo_pago, productos_vendidos)
        VALUES (:fecha, :cliente_id, :total, :pagado, :tipo_pago, :productos_vendidos)
        RETURNING id, total, pagado
    """)

    with engine.begin() as conn:
        result = conn.execute(insert_venta, {
            "fecha": fecha,
            "cliente_id": cliente_id,
            "total": total,
            "pagado": pagado,
            "tipo_pago": tipo_pago,
            "productos_vendidos": json.dumps(productos)
        })
        venta = result.mappings().fetchone()

        # Actualizar stock dentro de la misma transacción
        for item in productos:
            prod = get_product(item["id_producto"])
            if not prod:
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

    # 🔹 2️⃣ Ya fuera del bloque de transacción, crear la deuda (ahora sí existe venta_id)
    saldo_pendiente = round(float(total) - float(pagado), 2)
    if saldo_pendiente > 0:
        add_debt(
            cliente_id=cliente_id,
            monto=saldo_pendiente,
            venta_id=venta["id"],
            fecha=fecha,
            estado="pendiente",
            usuario=usuario,
            productos=productos
        )

    return dict(venta)

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

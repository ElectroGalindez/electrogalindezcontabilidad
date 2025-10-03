# backend/ventas.py
from datetime import datetime
from backend.db import engine
from sqlalchemy import text
from .logs import registrar_log
import uuid

def generar_id():
    return str(uuid.uuid4())[:8]

def register_sale(cliente_id, productos_vendidos, pagado=0.0, tipo_pago=None):
    total = sum(p["subtotal"] for p in productos_vendidos)
    venta_id = generar_id()

    with engine.begin() as conn:
        # Insertar venta
        conn.execute(
            text(
                "INSERT INTO ventas (id, cliente_id, total, pagado, tipo_pago, fecha) "
                "VALUES (:id, :cliente_id, :total, :pagado, :tipo_pago, NOW())"
            ),
            {"id": venta_id, "cliente_id": cliente_id, "total": total, "pagado": pagado, "tipo_pago": tipo_pago}
        )

        # Insertar productos vendidos
        for p in productos_vendidos:
            conn.execute(
                text(
                    "INSERT INTO productos_vendidos (venta_id, nombre, cantidad, precio_unitario, subtotal) "
                    "VALUES (:venta_id, :nombre, :cantidad, :precio_unitario, :subtotal)"
                ),
                {
                    "venta_id": venta_id,
                    "nombre": p["nombre"],
                    "cantidad": p["cantidad"],
                    "precio_unitario": p["precio_unitario"],
                    "subtotal": p["subtotal"]
                }
            )
    registrar_log("sistema", "registrar_venta", {"venta_id": venta_id})
    return {"id": venta_id, "cliente_id": cliente_id, "productos_vendidos": productos_vendidos, "total": total, "pagado": pagado, "tipo_pago": tipo_pago, "fecha": datetime.now().isoformat()}

def list_sales():
    with engine.connect() as conn:
        ventas_result = conn.execute(text("SELECT * FROM ventas ORDER BY fecha"))
        ventas_rows = [dict(row) for row in ventas_result]

        for venta in ventas_rows:
            productos_result = conn.execute(
                text("SELECT nombre, cantidad, precio_unitario, subtotal FROM productos_vendidos WHERE venta_id=:vid"),
                {"vid": venta["id"]}
            )
            venta["productos_vendidos"] = [dict(p) for p in productos_result]
    return ventas_rows

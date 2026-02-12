"""
Módulo para manejar deudas y pagos por producto en PostgreSQL.

Funciones públicas:
- list_debts()
- get_debt(deuda_id)
- add_debt(cliente_id, venta_id=None, productos=None, usuario=None)
- pay_debt_producto(deuda_id, producto_id, monto_pago, usuario=None)
- debts_by_client(cliente_id)
- delete_debt(deuda_id, usuario=None)
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import text
from .db import engine
from .clientes import update_debt
from backend.ventas import get_sale
from backend import ventas


# ======================================================
# 📜 Listar todas las deudas
# ======================================================
def list_debts() -> List[Dict[str, Any]]:
    query = text("SELECT * FROM deudas ORDER BY fecha DESC")
    with engine.connect() as conn:
        result = conn.execute(query)
        return [dict(row._mapping) for row in result]


# ======================================================
# 🔍 Obtener deuda con detalles
# ======================================================
def get_debt(deuda_id: int) -> Optional[Dict[str, Any]]:
    query = text("""
        SELECT d.id AS deuda_id, d.cliente_id, d.venta_id, d.monto_total, d.estado, d.fecha, d.descripcion,
               dd.id AS detalle_id, dd.producto_id, dd.cantidad, dd.precio_unitario, dd.estado AS estado_detalle
        FROM deudas d
        LEFT JOIN deudas_detalle dd ON d.id = dd.deuda_id
        WHERE d.id = :deuda_id
        ORDER BY dd.id
    """)
    with engine.connect() as conn:
        rows = conn.execute(query, {"deuda_id": deuda_id}).mappings().all()
        if not rows:
            return None

        deuda_info = dict(rows[0])
        detalles = []
        for r in rows:
            if r["detalle_id"] is not None:
                detalles.append({
                    "id": r["detalle_id"],
                    "producto_id": r["producto_id"],
                    "cantidad": r["cantidad"],
                    "precio_unitario": r["precio_unitario"],
                    "estado": r["estado_detalle"]
                })

        deuda_info["detalles"] = detalles

        # Quitar columnas repetidas de detalle
        for k in ["detalle_id", "producto_id", "cantidad", "precio_unitario", "estado_detalle"]:
            deuda_info.pop(k, None)

        return deuda_info

# ======================================================
# ➕ Crear deuda con detalles por producto
# ======================================================
def add_debt(
    cliente_id: int,
    venta_id: int = None,
    productos: list = None,  # lista de dicts: {id_producto, cantidad, precio_unitario}
    monto_total: float = 0.0,
    estado: str = "pendiente",
    usuario: str = None
) -> int:
    """
    Crea una deuda principal y registros por producto en deudas_detalle.
    """
    fecha = datetime.now()

    with engine.begin() as conn:
        # Insertar deuda principal
        query = text("""
            INSERT INTO deudas (cliente_id, venta_id, monto_total, estado, fecha, descripcion)
            VALUES (:cliente_id, :venta_id, :monto_total, :estado, :fecha, :descripcion)
            RETURNING id
        """)
        deuda_id = conn.execute(query, {
            "cliente_id": cliente_id,
            "venta_id": venta_id,
            "monto_total": monto_total,
            "estado": estado,
            "fecha": fecha,
            "descripcion": f"Deuda generada por venta {venta_id or 'N/A'}"
        }).scalar()

        # Insertar detalles por producto
        if productos:
            for p in productos:
                conn.execute(text("""
                    INSERT INTO deudas_detalle (deuda_id, producto_id, cantidad, precio_unitario, estado)
                    VALUES (:deuda_id, :producto_id, :cantidad, :precio_unitario, 'pendiente')
                """), {
                    "deuda_id": deuda_id,
                    "producto_id": p["id_producto"],
                    "cantidad": p["cantidad"],
                    "precio_unitario": p["precio_unitario"]
                })

    update_debt(cliente_id, monto_total)
    return deuda_id


# ======================================================
# 💵 Registrar pago de deuda por producto
# ======================================================
def pay_debt_producto(deuda_id: int, producto_id: int, monto_pago: float, usuario=None):
    deuda = get_debt(deuda_id)
    if not deuda:
        raise KeyError(f"Deuda {deuda_id} no encontrada")

    detalle = next(
        (d for d in deuda.get("detalles", [])
        if d.get("producto_id") == producto_id),
        None
    )

    if not detalle:
        raise KeyError(f"Producto {producto_id} no encontrado en la deuda {deuda_id}")

    precio_unitario = float(detalle["precio_unitario"])
    cantidad_pagada = monto_pago / precio_unitario
    nueva_cantidad = max(float(detalle["cantidad"]) - cantidad_pagada, 0)
    nuevo_estado_det = "pagado" if nueva_cantidad == 0 else "pendiente"

    with engine.begin() as conn:
        # Actualizar detalle
        conn.execute(text("""
            UPDATE deudas_detalle
            SET cantidad=:cantidad, estado=:estado
            WHERE id=:id
        """), {"cantidad": nueva_cantidad, "estado": nuevo_estado_det, "id": detalle["id"]})

        # Actualizar estado de deuda principal
        total_restante = conn.execute(text("""
            SELECT SUM(cantidad * precio_unitario)
            FROM deudas_detalle
            WHERE deuda_id=:deuda_id AND estado='pendiente'
        """), {"deuda_id": deuda_id}).scalar() or 0

        estado_deuda = "pagada" if total_restante <= 0 else "pendiente"
        conn.execute(text("""
            UPDATE deudas
            SET estado=:estado
            WHERE id=:deuda_id
        """), {"estado": estado_deuda, "deuda_id": deuda_id})

        # Actualizar venta asociada
        if total_restante <= 0:
            deuda["estado"] = "pagada"
            venta_id = deuda.get("venta_id")
            if venta_id:
                venta = get_sale(venta_id)
                if venta:
                    venta["pagado"] = venta["total"]
                    ventas.editar_venta_extra(
                        sale_id=venta_id,
                        observaciones=venta.get("observaciones"),
                        usuario=usuario
                    )

    return {"detalle": detalle, "estado_deuda": estado_deuda}


# ======================================================
# 📋 Listar deudas por cliente
# ======================================================
def debts_by_client(cliente_id: int):
    query = text("""
        SELECT d.id AS deuda_id, d.cliente_id, d.venta_id, d.monto_total, d.estado, d.fecha, d.descripcion,
               dd.id AS detalle_id, dd.producto_id, dd.cantidad, dd.precio_unitario, dd.estado AS estado_detalle
        FROM deudas d
        LEFT JOIN deudas_detalle dd ON d.id = dd.deuda_id
        WHERE d.cliente_id = :cliente_id
        ORDER BY d.fecha DESC, dd.id
    """)
    with engine.connect() as conn:
        rows = conn.execute(query, {"cliente_id": cliente_id}).mappings().all()
        if not rows:
            return []

        deudas_map = {}
        for r in rows:
            d_id = r["deuda_id"]
            if d_id not in deudas_map:
                deudas_map[d_id] = dict(r)
                deudas_map[d_id]["detalles"] = []

            if r["detalle_id"] is not None:
                deudas_map[d_id]["detalles"].append({
                    "id": r["detalle_id"],
                    "producto_id": r["producto_id"],
                    "cantidad": r["cantidad"],
                    "precio_unitario": r["precio_unitario"],
                    "estado": r["estado_detalle"]
                })

        # Limpiar columnas repetidas de detalle
        for deuda in deudas_map.values():
            for k in ["detalle_id", "producto_id", "cantidad", "precio_unitario", "estado_detalle"]:
                deuda.pop(k, None)

        return list(deudas_map.values())

# ======================================================
# 🗑️ Eliminar deuda
# ======================================================
def delete_debt(deuda_id: int, usuario: Optional[str] = None) -> bool:
    deuda = get_debt(deuda_id)
    if not deuda:
        return False

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM deudas_detalle WHERE deuda_id=:id"), {"id": deuda_id})
        conn.execute(text("DELETE FROM deudas WHERE id=:id"), {"id": deuda_id})

    update_debt(deuda["cliente_id"], -float(deuda["monto_total"]))

    try:
        from .logs import registrar_log
        registrar_log(usuario or "sistema", "eliminar_deuda", {
            "deuda_id": deuda_id,
            "cliente_id": deuda["cliente_id"],
            "monto_total": deuda["monto_total"]
        })
    except Exception:
        pass

    return True


# ======================================================
# 📊 Listar todos los detalles de deudas
# ======================================================
def list_detalle_deudas():
    query = text("""
        SELECT dd.id AS detalle_id, dd.deuda_id, dd.producto_id, dd.cantidad, dd.precio_unitario, dd.estado,
               d.cliente_id, d.fecha, d.monto_total, d.estado AS estado_deuda
        FROM deudas_detalle dd
        JOIN deudas d ON d.id = dd.deuda_id
        ORDER BY d.fecha DESC
    """)
    with engine.connect() as conn:
        return [dict(row._mapping) for row in conn.execute(query)]


# ======================================================
# 📋 Listar clientes con deudas pendientes
# ======================================================
def list_clientes_con_deuda():
    query = text("""
        SELECT DISTINCT c.id, c.nombre, c.deuda_total
        FROM clientes c
        JOIN deudas d ON c.id = d.cliente_id
        WHERE d.estado='pendiente' AND c.deuda_total>0
        ORDER BY c.nombre
    """)
    with engine.connect() as conn:
        return [dict(row._mapping) for row in conn.execute(query)]

def generar_factura_pago_deuda(cliente, productos_pagados):
    from io import BytesIO
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height-50, f"Factura de Pago de Deuda - Cliente: {cliente.get('nombre','N/A')}")

    y = height-100
    c.setFont("Helvetica", 12)
    for p in productos_pagados:
        c.drawString(50, y, f"{p['nombre']} - Cantidad: {p['cantidad']} - Precio: ${p['precio_unitario']:.2f}")
        y -= 20

    total = sum(p['cantidad']*p['precio_unitario'] for p in productos_pagados)
    c.drawString(50, y-20, f"Total pagado: ${total:.2f}")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

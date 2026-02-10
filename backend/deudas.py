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
import json

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
        SELECT d.*, json_agg(dd.*) AS detalles
        FROM deudas d
        LEFT JOIN deudas_detalle dd ON d.id = dd.deuda_id
        WHERE d.id = :id
        GROUP BY d.id
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"id": deuda_id}).mappings().first()
        if result:
            r = dict(result)
            # Convertir detalles de string JSON a lista si es necesario
            if isinstance(r["detalles"], str):
                r["detalles"] = json.loads(r["detalles"])
            return r
        return None

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
    Crea una deuda general y registros por producto en deudas_detalle.
    """
    fecha = datetime.now()
    productos_json = json.dumps(productos or [])

    with engine.begin() as conn:
        # Insertar deuda principal
        query = text("""
            INSERT INTO deudas (cliente_id, venta_id, monto_total, estado, fecha, descripcion, productos)
            VALUES (:cliente_id, :venta_id, :monto_total, :estado, :fecha, :descripcion, :productos)
            RETURNING id
        """)
        deuda_id = conn.execute(query, {
            "cliente_id": cliente_id,
            "venta_id": venta_id,
            "monto_total": monto_total,
            "estado": estado,
            "fecha": fecha,
            "descripcion": f"Deuda generada por venta {venta_id or 'N/A'}",
            "productos": productos_json
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

    # Actualizar deuda total del cliente
    update_debt(cliente_id, monto_total)
    return deuda_id

# ======================================================
# 💵 Registrar pago de deuda por producto
# ======================================================
def pay_debt_producto(deuda_id: int, producto_id: int, monto_pago: float, usuario: Optional[str] = None) -> Dict[str, Any]:
    """
    Aplica un pago solo sobre un detalle de deuda (producto) específico.
    Actualiza la cantidad pendiente proporcionalmente al pago.
    """
    deuda = get_debt(deuda_id)
    if not deuda:
        raise KeyError(f"Deuda {deuda_id} no encontrada")

    detalle = next((d for d in deuda.get("detalles", []) if d["producto_id"] == producto_id), None)
    if not detalle:
        raise KeyError(f"Producto {producto_id} no encontrado en la deuda {deuda_id}")

    cantidad_pendiente = float(detalle["cantidad"])
    precio_unitario = float(detalle["precio_unitario"])
    monto_total_pendiente = cantidad_pendiente * precio_unitario

    if monto_pago <= 0 or monto_pago > monto_total_pendiente:
        raise ValueError(f"Monto de pago inválido. Debe ser entre 0 y {monto_total_pendiente}")

    # -----------------------------
    # Calcular cantidad pagada y nueva cantidad pendiente
    # -----------------------------
    cantidad_pagada = monto_pago / precio_unitario
    nueva_cantidad = round(max(cantidad_pendiente - cantidad_pagada, 0), 4)

    nuevo_estado_det = "pagado" if nueva_cantidad == 0 else "pendiente"

    with engine.begin() as conn:
        # Actualizar detalle de deuda
        conn.execute(text("""
            UPDATE deudas_detalle
            SET cantidad = :nueva_cantidad, estado = :nuevo_estado
            WHERE id = :id
        """), {"nueva_cantidad": nueva_cantidad, "nuevo_estado": nuevo_estado_det, "id": detalle["id"]})

        # Actualizar deuda principal
        nuevo_monto_total = round(float(deuda["monto_total"]) - monto_pago, 2)
        nuevo_estado = "pagada" if nuevo_monto_total == 0 else "pendiente"
        result = conn.execute(text("""
            UPDATE deudas
            SET monto_total=:nuevo_monto_total, estado=:nuevo_estado
            WHERE id=:id
            RETURNING *
        """), {"nuevo_monto_total": nuevo_monto_total, "nuevo_estado": nuevo_estado, "id": deuda_id}).mappings().first()

    # Actualizar deuda total del cliente
    update_debt(deuda["cliente_id"], -monto_pago)

    # Registrar log
    try:
        from .logs import registrar_log
        registrar_log(usuario or "sistema", "pago_deuda_producto", {
            "deuda_id": deuda_id,
            "cliente_id": deuda["cliente_id"],
            "producto_id": producto_id,
            "monto_pago": monto_pago,
            "cantidad_pagada": cantidad_pagada,
            "cantidad_restante": nueva_cantidad,
            "estado_final": nuevo_estado_det
        })
    except Exception:
        pass

    return dict(result)

# ======================================================
# 📋 Listar deudas por cliente
# ======================================================
def debts_by_client(cliente_id: int):
    query = text("""
        SELECT d.id, d.fecha, d.estado, d.monto_total, d.descripcion, 
               json_agg(dd.*) AS detalles
        FROM deudas d
        LEFT JOIN deudas_detalle dd ON d.id = dd.deuda_id
        WHERE d.cliente_id = :cliente_id
        GROUP BY d.id
        ORDER BY d.fecha DESC
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"cliente_id": cliente_id})
        return [dict(row._mapping) for row in result]

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
# 📊 Listar todos los detalles de deudas (deudas_detalle)
# ======================================================
def list_detalle_deudas():
    """
    Devuelve una lista de todos los detalles de deuda, 
    incluyendo datos del cliente, monto, estado y fecha.
    """
    query = text("""
        SELECT 
            dd.id AS detalle_id,
            dd.deuda_id,
            dd.producto_id,
            dd.cantidad,
            dd.precio_unitario,
            dd.estado,
            d.cliente_id,
            d.fecha,
            d.monto_total,
            d.estado AS estado_deuda
        FROM deudas_detalle dd
        JOIN deudas d ON d.id = dd.deuda_id
        ORDER BY d.fecha DESC
    """)
    with engine.connect() as conn:
        result = conn.execute(query)
        return [dict(row._mapping) for row in result]


# ======================================================
# 📋 Listar clientes con deudas pendiente
# ======================================================
def list_clientes_con_deuda():
    """
    Devuelve una lista de clientes que tienen deudas pendientes.
    """
    query = text("""
        SELECT DISTINCT c.id, c.nombre, c.deuda_total
        FROM clientes c
        JOIN deudas d ON c.id = d.cliente_id
        WHERE d.estado = 'pendiente' AND c.deuda_total > 0
        ORDER BY c.nombre
    """)
    with engine.connect() as conn:
        result = conn.execute(query)
        return [dict(row._mapping) for row in result]

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO
import os

def generar_factura_pago_deuda(cliente: dict, detalle_deuda: dict, monto_pagado: float, logo_path="assets/logo.png"):
    """
    Genera un PDF de comprobante de pago de deuda.
    
    cliente: dict con info del cliente
    detalle_deuda: dict con info de deuda/detalle producto pagado
    monto_pagado: float con el monto pagado
    logo_path: ruta al logo de la empresa
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    line_height = 15

    # Cargar logo
    logo = None
    if os.path.exists(logo_path):
        try:
            logo = ImageReader(logo_path)
        except Exception as e:
            print(f"No se pudo cargar el logo: {e}")

    def dibujar_factura(y_offset=0):
        nonlocal c
        # ---------------- Logo ----------------
        if logo:
            c.drawImage(logo, 40, height - 85 - y_offset, width=80, height=70, preserveAspectRatio=True)
        # ------------- Empresa ----------------
        c.setFont("Helvetica-Bold", 14)
        c.drawString(130, height - 50 - y_offset, "Omar Galíndez Ramirez. CI: 85082506984")
        c.setFont("Helvetica", 10)
        c.drawString(130, height - 65 - y_offset, f"Comprobante de pago de deuda")
        c.drawString(130, height - 80 - y_offset, f"Fecha: {detalle_deuda.get('fecha','')}")

        # ------------- Cliente ----------------
        col1_x = 40
        row_y = height - 110 - y_offset
        c.drawString(col1_x, row_y, f"Cliente: {cliente.get('nombre','')}"); row_y -= line_height
        c.drawString(col1_x, row_y, f"CI: {cliente.get('ci','')}"); row_y -= line_height
        c.drawString(col1_x, row_y, f"Teléfono: {cliente.get('telefono','')}"); row_y -= line_height

        # ------------- Pago ----------------
        col2_x = 320
        row_y2 = height - 110 - y_offset
        c.drawString(col2_x, row_y2, f"Producto: {detalle_deuda.get('producto','')}"); row_y2 -= line_height
        c.drawString(col2_x, row_y2, f"Cantidad pagada: {detalle_deuda.get('cantidad_pagada',detalle_deuda.get('cantidad',0))}"); row_y2 -= line_height
        c.drawString(col2_x, row_y2, f"Monto pagado: ${monto_pagado:,.2f}"); row_y2 -= line_height
        c.drawString(col2_x, row_y2, f"Saldo restante: ${detalle_deuda.get('monto_restante',0):,.2f}"); row_y2 -= line_height

        # ------------- Firma ----------------
        firma_y = row_y2 - 40
        c.drawString(40, firma_y, "__________________________")
        c.drawString(40, firma_y - 10, "Firma Cliente")
        c.drawString(320, firma_y, "__________________________")
        c.drawString(320, firma_y - 10, "Firma Empresa")

    # Dibujar dos facturas en la misma hoja
    dibujar_factura(y_offset=0)
    c.setStrokeColor(colors.gray)
    c.setLineWidth(1)
    c.line(40, height/2, width-40, height/2)
    dibujar_factura(y_offset=height/2)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

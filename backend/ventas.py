# backend/ventas.py
from typing import Dict, Optional
from datetime import datetime
from sqlalchemy import text
from backend.db import engine
from .productos import get_product, update_product, increment_stock
from .logs import registrar_log
import json
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# ----------------------------
# Registrar venta
# ----------------------------
from .productos import adjust_stock  # o decrement_stock según tu implementación

def register_sale(
    cliente_id: Optional[str],
    productos_vendidos: list,
    total: float,
    pagado: float,
    saldo: float,
    tipo_pago: str,
    observaciones: Optional[str] = None,
    vendedor: Optional[str] = None,
    telefono_vendedor: Optional[str] = None,
    chofer: Optional[str] = None,
    chapa: Optional[str] = None,
    usuario: Optional[str] = None
) -> dict:
    with engine.begin() as conn:
        # 1️⃣ Insertar la venta
        insert_query = text("""
            INSERT INTO ventas (
                cliente_id, productos_vendidos, total, pagado, saldo,
                tipo_pago, observaciones, vendedor, telefono_vendedor, chofer, chapa
            ) VALUES (
                :cliente_id, :productos_vendidos, :total, :pagado, :saldo,
                :tipo_pago, :observaciones, :vendedor, :telefono_vendedor, :chofer, :chapa
            )
            RETURNING *
        """)
        result = conn.execute(insert_query, {
            "cliente_id": cliente_id,
            "productos_vendidos": json.dumps(productos_vendidos),
            "total": total,
            "pagado": pagado,
            "saldo": saldo,
            "tipo_pago": tipo_pago,
            "observaciones": observaciones,
            "vendedor": vendedor,
            "telefono_vendedor": telefono_vendedor,
            "chofer": chofer,
            "chapa": chapa
        }).mappings().first()

        if not result:
            raise Exception("Error al registrar la venta")

        venta = dict(result)

        # 2️⃣ ⚡ Descontar stock de los productos vendidos
        for item in productos_vendidos:
            producto_id = item.get("id_producto")
            cantidad = item.get("cantidad", 0)
            if producto_id and cantidad > 0:
                adjust_stock(producto_id, -cantidad)  # descontar del inventario

        # 3️⃣ Registrar log
        registrar_log(usuario or "sistema", "registrar_venta", venta)
        return venta

# ----------------------------
# Obtener venta por ID
# ----------------------------
def get_sale(sale_id: str) -> Optional[Dict]:
    query = text("SELECT * FROM ventas WHERE id = :id")
    with engine.connect() as conn:
        result = conn.execute(query, {"id": sale_id}).mappings().first()
    if result:
        r = dict(result)
        productos_vendidos = r.get("productos_vendidos") or "[]"
        if isinstance(productos_vendidos, str):
            try:
                productos_vendidos = json.loads(productos_vendidos)
            except:
                productos_vendidos = []
        r["productos_vendidos"] = productos_vendidos
        return r
    return None

# ----------------------------
# Eliminar venta
# ----------------------------
def delete_sale(sale_id: str, usuario: Optional[str] = None) -> bool:
    """Elimina una venta por su ID y devuelve productos al stock"""
    sale = get_sale(sale_id)
    if not sale:
        return False

    # Devolver productos al stock
    for item in sale.get("productos_vendidos", []):
        increment_stock(item["id_producto"], item["cantidad"])

    # Eliminar la venta de la BD
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM ventas WHERE id = :id"), {"id": sale_id})

    registrar_log(usuario or "sistema", "eliminar_venta", {"venta_id": sale_id, "venta": sale})
    return True

# ----------------------------
# Editar campos extras de venta
# ----------------------------
def editar_venta_extra(
    sale_id: str,
    observaciones: Optional[str] = None,
    vendedor: Optional[str] = None,
    telefono_vendedor: Optional[str] = None,
    chofer: Optional[str] = None,
    chapa: Optional[str] = None,
    usuario: Optional[str] = None
):
    with engine.begin() as conn:
        update_query = text("""
            UPDATE ventas
            SET observaciones = COALESCE(:observaciones, observaciones),
                vendedor = COALESCE(:vendedor, vendedor),
                telefono_vendedor = COALESCE(:telefono_vendedor, telefono_vendedor),
                chofer = COALESCE(:chofer, chofer),
                chapa = COALESCE(:chapa, chapa)
            WHERE id = :id
            RETURNING *
        """)
        updated = conn.execute(update_query, {
            "id": sale_id,
            "observaciones": observaciones,
            "vendedor": vendedor,
            "telefono_vendedor": telefono_vendedor,
            "chofer": chofer,
            "chapa": chapa
        }).mappings().first()
        if updated:
            registrar_log(usuario or "sistema", "editar_venta_extra", dict(updated))
            return dict(updated)
    return None

# ----------------------------
# Listar ventas
# ----------------------------
def list_sales():
    query = text("SELECT * FROM ventas ORDER BY fecha DESC")
    with engine.connect() as conn:
        resultados = conn.execute(query).mappings().all()

    ventas_list = []
    for r in resultados:
        productos_vendidos = r.get("productos_vendidos") or "[]"
        if isinstance(productos_vendidos, str):
            try:
                productos_vendidos = json.loads(productos_vendidos)
            except:
                productos_vendidos = []
        r_dict = dict(r)
        r_dict["productos_vendidos"] = productos_vendidos
        ventas_list.append(r_dict)
    return ventas_list

def listar_ventas_dict():
    """Devuelve un diccionario legible con todas las ventas"""
    ventas_list = list_sales()
    return {f"ID {v['id']} - Cliente {v.get('cliente_id','N/A')} - Total ${v.get('total',0):.2f}": v for v in ventas_list}

# ----------------------------
# Generar PDF
# ----------------------------
def generar_factura_pdf(venta, cliente, productos_vendidos, gestor_info=None, logo_path="assets/logo.png"):
    """
    Genera factura profesional en PDF, duplicada en la misma hoja
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    line_height = 15
    logo = ImageReader(logo_path) if os.path.exists(logo_path) else None

    def dibujar_factura(y_offset=0):
        nonlocal c
        # Aquí tu código para dibujar la factura, igual que tu versión actual
        # ...
        pass  # Mantener tu implementación actual del PDF

    dibujar_factura(y_offset=0)
    c.setStrokeColor(colors.gray)
    c.setLineWidth(1)
    c.line(40, height/2, width-40, height/2)
    dibujar_factura(y_offset=height/2)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

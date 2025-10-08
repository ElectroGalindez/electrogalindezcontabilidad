# backend/ventas.py
from typing import  Dict, Optional
from datetime import datetime
from sqlalchemy import text
from backend.db import engine
from .productos import  get_product, update_product
from .logs import registrar_log
import json

# ------------------------------
# Registrar venta
# ----------------------------
def register_sale(cliente_id, total, pagado, usuario, tipo_pago, productos=None):
    """
    Registra una venta, descuenta del inventario y guarda productos vendidos como JSON.
    """
    fecha = datetime.now()
    productos_data = []

    with engine.begin() as conn:
        # Preparar productos para guardar en JSON
        if productos:
            for item in productos:
                prod_id = item.get("id_producto") or item.get("id")
                cantidad_vendida = float(item.get("cantidad", 0))
                precio_unitario = float(item.get("precio_unitario", 0.0))
                subtotal = cantidad_vendida * precio_unitario

                productos_data.append({
                    "id_producto": prod_id,
                    "nombre": item.get("nombre"),
                    "cantidad": cantidad_vendida,
                    "precio_unitario": precio_unitario,
                    "subtotal": subtotal
                })

                # Actualizar stock
                producto = get_product(prod_id)
                if producto:
                    stock_actual = float(producto.get("cantidad", 0))
                    nuevo_stock = max(stock_actual - cantidad_vendida, 0)
                    update_product(prod_id, nombre=producto["nombre"], cantidad=nuevo_stock, precio=producto["precio"])

        # Guardar venta con productos en JSON
        query_venta = text("""
            INSERT INTO ventas (cliente_id, total, pagado, usuario, tipo_pago, fecha, productos_vendidos)
            VALUES (:cliente_id, :total, :pagado, :usuario, :tipo_pago, :fecha, :productos_vendidos)
            RETURNING id
        """)
        venta_id = conn.execute(query_venta, {
            "cliente_id": cliente_id,
            "total": total,
            "pagado": pagado,
            "usuario": usuario,
            "tipo_pago": tipo_pago,
            "fecha": fecha,
            "productos_vendidos": json.dumps(productos_data)  # 🔹 Aquí se guarda el detalle
        }).scalar()

        registrar_log(usuario, "registrar_venta", {"venta_id": venta_id, "total": total, "pagado": pagado})

    return {"id": venta_id, "total": total, "pagado": pagado, "fecha": fecha, "productos_vendidos": productos_data}

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
            except json.JSONDecodeError:
                productos_vendidos = []

        r_dict = dict(r)
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

def listar_ventas_dict():
    ventas = list_sales()
    ventas_dict = {f"ID {v['id']} - Cliente {v['cliente_id']} - Total ${v['total']}": v for v in ventas}
    return ventas_dict




from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

def generar_factura_pdf(venta, cliente, productos_vendidos, gestor_info=None):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    margen_x = 40
    y = height - 50

    # Encabezado
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margen_x, y, "ElectroGalíndez S.A.")
    y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(margen_x, y, f"Factura N°: {venta.get('numero', venta.get('id','N/A'))}")
    y -= 15
    fecha = str(venta.get('fecha','N/A'))
    c.drawString(margen_x, y, f"Fecha: {fecha}")
    y -= 20

    # Datos del cliente (valores por defecto si faltan)
    cliente_nombre = cliente.get("nombre", "N/A")
    cliente_carnet = cliente.get("carnet", "N/A")
    cliente_identidad = cliente.get("identidad", "N/A")
    cliente_chapa = cliente.get("chapa", "N/A")

    c.setFont("Helvetica-Bold", 10)
    c.drawString(margen_x, y, "Cliente:")
    c.setFont("Helvetica", 10)
    c.drawString(margen_x + 60, y, str(cliente_nombre))
    y -= 15
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margen_x, y, "Carnet/ID:")
    c.setFont("Helvetica", 10)
    c.drawString(margen_x + 60, y, str(cliente_carnet))
    y -= 15
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margen_x, y, "Identidad:")
    c.setFont("Helvetica", 10)
    c.drawString(margen_x + 60, y, str(cliente_identidad))
    y -= 15
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margen_x, y, "Chapa:")
    c.setFont("Helvetica", 10)
    c.drawString(margen_x + 60, y, str(cliente_chapa))
    y -= 25

    # Productos
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margen_x, y, "Producto")
    c.drawString(margen_x + 200, y, "Cantidad")
    c.drawString(margen_x + 270, y, "Precio Unitario")
    c.drawString(margen_x + 370, y, "Subtotal")
    y -= 15
    c.setFont("Helvetica", 10)

    if not productos_vendidos:
        c.drawString(margen_x, y, "Ningún producto registrado")
        y -= 15
    else:
        for p in productos_vendidos:
            nombre = str(p.get("nombre", "N/A"))
            cantidad = p.get("cantidad") or 0
            precio = p.get("precio_unitario") or 0.0
            subtotal = cantidad * precio

            c.drawString(margen_x, y, nombre)
            c.drawString(margen_x + 200, y, str(cantidad))
            c.drawString(margen_x + 270, y, f"${precio:.2f}")
            c.drawString(margen_x + 370, y, f"${subtotal:.2f}")
            y -= 15

    y -= 10
    # Totales (con valores por defecto)
    total = venta.get('total') or 0.0
    pagado = venta.get('pagado') or 0.0
    saldo = venta.get('saldo') or 0.0
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margen_x, y, f"Total: ${total:.2f}")
    y -= 15
    c.drawString(margen_x, y, f"Pagado: ${pagado:.2f}")
    y -= 15
    c.drawString(margen_x, y, f"Saldo pendiente: ${saldo:.2f}")
    y -= 20

    # Método de pago
    metodo = ", ".join(venta.get("desglose_pago", {}).keys()) or "N/A"
    c.drawString(margen_x, y, f"Método de pago: {metodo}")
    y -= 20

    # Observaciones
    obs = venta.get("observaciones") or ""
    if obs:
        c.drawString(margen_x, y, f"Observaciones: {obs}")
        y -= 20

    # Vendedor / Chofer
    if gestor_info:
        c.drawString(margen_x, y, f"Vendedor: {gestor_info.get('vendedor','N/A')}")
        c.drawString(margen_x + 200, y, f"Chofer: {gestor_info.get('chofer','N/A')}")
        y -= 20

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

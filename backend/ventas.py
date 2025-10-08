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
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

def generar_factura_pdf(venta, cliente, productos_vendidos, gestor_info=None):
    """
    Genera una factura profesional en PDF mostrando todos los productos de la venta.
    
    - venta: dict con info de la venta (id, numero, fecha, total, pagado, saldo, observaciones, desglose_pago)
    - cliente: dict con info del cliente (nombre, ci, chapa, direccion, telefono)
    - productos_vendidos: lista de dicts {nombre, cantidad, precio_unitario}
    - gestor_info: dict opcional con datos del vendedor/chofer
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    elements = []
    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleB = styles['Heading2']

    # ---------------------------
    # Encabezado
    # ---------------------------
    elements.append(Paragraph("ElectroGalíndez S.A.", styleB))
    elements.append(Paragraph(f"Factura N°: {venta.get('numero', venta.get('id',''))}", styleN))
    elements.append(Paragraph(f"Fecha: {str(venta.get('fecha',''))}", styleN))
    elements.append(Spacer(1, 12))

    # ---------------------------
    # Datos del cliente
    # ---------------------------
    cliente_nombre = cliente.get("nombre", "N/A")
    cliente_ci = cliente.get("ci", "N/A")          # mapeado correctamente
    cliente_chapa = cliente.get("chapa", "N/A")    # mapeado correctamente
    cliente_direccion = cliente.get("direccion", "N/A")
    cliente_telefono = cliente.get("telefono", "N/A")

    elements.append(Paragraph(f"<b>Cliente:</b> {cliente_nombre}", styleN))
    elements.append(Paragraph(f"<b>Carnet/ID:</b> {cliente_ci}", styleN))
    elements.append(Paragraph(f"<b>Chapa:</b> {cliente_chapa}", styleN))
    elements.append(Paragraph(f"<b>Dirección:</b> {cliente_direccion}", styleN))
    elements.append(Paragraph(f"<b>Teléfono:</b> {cliente_telefono}", styleN))
    elements.append(Spacer(1, 12))

    # ---------------------------
    # Productos
    # ---------------------------
    table_data = [["Producto", "Cantidad", "Precio Unitario", "Subtotal"]]
    for p in productos_vendidos:
        nombre = p.get("nombre", "N/A")
        cantidad = float(p.get("cantidad", 0) or 0)
        precio_unitario = float(p.get("precio_unitario", 0.0) or 0.0)
        subtotal = cantidad * precio_unitario
        table_data.append([nombre, str(cantidad), f"${precio_unitario:.2f}", f"${subtotal:.2f}"])

    t = Table(table_data, colWidths=[200, 80, 100, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.gray),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(1,1),(-1,-1),'CENTER'),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
    ]))
    elements.append(t)
    elements.append(Spacer(1, 12))

    # ---------------------------
    # Totales y pagos
    # ---------------------------
    total = float(venta.get("total", 0.0) or 0.0)
    pagado = float(venta.get("pagado", 0.0) or 0.0)
    saldo = float(venta.get("saldo", 0.0) or 0.0)

    elements.append(Paragraph(f"<b>Total:</b> ${total:.2f}", styleN))
    elements.append(Paragraph(f"<b>Pagado:</b> ${pagado:.2f}", styleN))
    elements.append(Paragraph(f"<b>Saldo pendiente:</b> ${saldo:.2f}", styleN))
    elements.append(Spacer(1, 12))

    # Método de pago
    metodo_pago = ", ".join(venta.get("desglose_pago", {}).keys()) or "N/A"
    elements.append(Paragraph(f"<b>Método de pago:</b> {metodo_pago}", styleN))
    elements.append(Spacer(1, 12))

    # Observaciones
    observaciones = venta.get("observaciones","")
    if observaciones:
        elements.append(Paragraph(f"<b>Observaciones:</b> {observaciones}", styleN))
        elements.append(Spacer(1, 12))

    # Vendedor / Chofer
    if gestor_info:
        vendedor = gestor_info.get("vendedor","N/A")
        chofer = gestor_info.get("chofer","N/A")
        elements.append(Paragraph(f"<b>Vendedor:</b> {vendedor}", styleN))
        elements.append(Paragraph(f"<b>Chofer:</b> {chofer}", styleN))

    # ---------------------------
    # Construir PDF
    # ---------------------------
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

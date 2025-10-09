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
from reportlab.platypus import Table, TableStyle
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import os

def generar_factura_pdf(venta, cliente, productos_vendidos, gestor_info=None, logo_path=None):
    """
    Genera una factura profesional en PDF mostrando todos los productos de la venta,
    duplicada en la misma hoja (para cliente y archivo interno).
    
    venta: dict con info de la venta
    cliente: dict con info del cliente
    productos_vendidos: lista de dicts {nombre, cantidad, precio_unitario}
    gestor_info: dict opcional con datos del vendedor/chofer
    logo_path: ruta opcional a logo de la empresa
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleB = styles['Heading2']

    # ---------------------------
    # Función para dibujar cada factura
    # ---------------------------
    def dibujar_factura(y_offset=0):
        nonlocal c
        
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, height - 50 - y_offset, "Omar Galíndez Ramirez. CI: 85082506984")
        c.setFont("Helvetica", 10)
        c.drawString(100, height - 65 - y_offset, f"Factura N°: {venta.get('numero', venta.get('id',''))}")
        c.drawString(100, height - 80 - y_offset, f"Fecha: {str(venta.get('fecha',''))}")


        # ---------------------------
        # Columnas: Cliente y Totales
        # ---------------------------
        c.setFont("Helvetica", 9)
        col1_x = 40
        col2_x = 320
        row_y = height - 110 - y_offset
        line_height = 15

        # Columna 1: Cliente
        cliente_nombre = cliente.get("nombre") or ""
        cliente_ci = cliente.get("ci") or ""
        cliente_chapa = cliente.get("chapa") or ""
        cliente_direccion = cliente.get("direccion") or ""
        cliente_telefono = cliente.get("telefono") or ""

        c.drawString(col1_x, row_y, f"Cliente: {cliente_nombre}"); row_y -= line_height
        c.drawString(col1_x, row_y, f"Carnet/ID: {cliente_ci}"); row_y -= line_height
        c.drawString(col1_x, row_y, f"Chapa: {cliente_chapa}"); row_y -= line_height
        c.drawString(col1_x, row_y, f"Dirección: {cliente_direccion}"); row_y -= line_height
        c.drawString(col1_x, row_y, f"Teléfono: {cliente_telefono}")



        # Columna 2: Totales y pagos
        total = float(venta.get("total") or 0.0)
        pagado = float(venta.get("pagado") or 0.0)
        saldo = float(venta.get("saldo") or 0.0)
        metodo_pago = venta.get("tipo_pago") or ""
        vendedor = gestor_info.get("vendedor","") if gestor_info else ""
        chofer = gestor_info.get("chofer","") if gestor_info else ""
        observaciones = venta.get("observaciones","")
        # ---------------------------
        # Totales y pagos
        # ---------------------------
        total = float(venta.get("total") or 0.0)
        pagado_usd = float(venta.get("pagado") or 0.0)
        tasa_cup = 120
        pagado_cup = pagado_usd * tasa_cup

        # Mostrar Pagado en USD y CUP
        pagado_str = f"(USD) {pagado_usd:,.2f} - (CUP) {pagado_cup:,.2f}"

        row_y2 = height - 110 - y_offset
        c.drawString(col2_x, row_y2, f"Total: ${total:.2f}"); row_y2 -= line_height
        c.drawString(col2_x, row_y2, f"Pagado: {pagado_str}"); row_y2 -= line_height
        c.drawString(col2_x, row_y2, f"Saldo pendiente: ${saldo:.2f}"); row_y2 -= line_height
        c.drawString(col2_x, row_y2, f"Método de pago: {metodo_pago}"); row_y2 -= line_height
        if observaciones:
            c.drawString(col2_x, row_y2, f"Observaciones: {observaciones}"); row_y2 -= line_height
        c.drawString(col2_x, row_y2, f"Vendedor: {vendedor}"); row_y2 -= line_height
        c.drawString(col2_x, row_y2, f"Chofer: {chofer}")

        # ---------------------------
        # Separación antes de la tabla
        # ---------------------------
        table_y_start = row_y - 40  # espacio extra para separar del chofer

        # ---------------------------
        # Tabla de productos
        # ---------------------------
        table_data = [["Producto", "Cantidad", "Precio Unitario", "Subtotal"]]
        for p in productos_vendidos:
            nombre = p.get("nombre","")
            cantidad = float(p.get("cantidad") or 0)
            precio_unitario = float(p.get("precio_unitario") or 0)
            subtotal = cantidad * precio_unitario
            table_data.append([nombre, str(int(cantidad)), f"${precio_unitario:.2f}", f"${subtotal:.2f}"])

        table = Table(table_data, colWidths=[200, 80, 100, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.gray),
            ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
            ('ALIGN',(1,1),(-1,-1),'CENTER'),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
        ]))
        table.wrapOn(c, 40, table_y_start)
        table.drawOn(c, 40, table_y_start - len(table_data)*18)

        # ---------------------------
        # Firma doble al final
        # ---------------------------
        firma_y = table_y_start - len(table_data)*18 - 60
        c.drawString(40, firma_y, "__________________________")
        c.drawString(40, firma_y - 12, "Firma Cliente")
        c.drawString(320, firma_y, "__________________________")
        c.drawString(320, firma_y - 12, "Firma Vendedor")

    # ---------------------------
    # Dibujar dos facturas en la misma hoja
    # ---------------------------
    dibujar_factura(y_offset=0)
    # Línea divisoria
    c.setStrokeColor(colors.gray)
    c.setLineWidth(1)
    c.line(40, height/2, width-40, height/2)
    dibujar_factura(y_offset=height/2)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

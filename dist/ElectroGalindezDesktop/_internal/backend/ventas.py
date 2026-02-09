"""Sales management helpers and PDF invoice generation."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
import json
import os
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle

from core.paths import resolve_asset_path
from .db import get_connection
from .logs import registrar_log
from .productos import get_product, update_product


def _serialize_productos(productos: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Convert raw product input into normalized sale details."""
    productos_data: List[Dict[str, Any]] = []
    if not productos:
        return productos_data

    for item in productos:
        prod_id = item.get("id_producto") or item.get("id")
        cantidad_vendida = float(item.get("cantidad", 0))
        precio_unitario = float(item.get("precio_unitario", 0.0))
        subtotal = cantidad_vendida * precio_unitario

        productos_data.append(
            {
                "id_producto": prod_id,
                "nombre": item.get("nombre"),
                "cantidad": cantidad_vendida,
                "precio_unitario": precio_unitario,
                "subtotal": subtotal,
            }
        )

        producto = get_product(prod_id)
        if producto:
            stock_actual = float(producto.get("cantidad", 0))
            nuevo_stock = max(stock_actual - cantidad_vendida, 0)
            update_product(
                prod_id,
                nombre=producto["nombre"],
                cantidad=nuevo_stock,
                precio=producto["precio"],
            )

    return productos_data


def _deserialize_productos(value: Any) -> List[Dict[str, Any]]:
    """Ensure productos_vendidos is a list of dictionaries."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return []
    return []


def _normalize_fecha(value: Any) -> Any:
    """Normalize stored date values to datetime when possible."""
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return value
    return value


def register_sale(cliente_id, total, pagado, usuario, tipo_pago, productos=None):
    """Registrar una venta, ajustar inventario y persistir productos vendidos."""
    fecha = datetime.now().isoformat()
    productos_data = _serialize_productos(productos)

    with get_connection() as conn:
        query_venta = """
            INSERT INTO ventas (cliente_id, total, pagado, usuario, tipo_pago, fecha, productos_vendidos)
            VALUES (:cliente_id, :total, :pagado, :usuario, :tipo_pago, :fecha, :productos_vendidos)
        """
        cursor = conn.execute(
            query_venta,
            {
                "cliente_id": cliente_id,
                "total": total,
                "pagado": pagado,
                "usuario": usuario,
                "tipo_pago": tipo_pago,
                "fecha": fecha,
                "productos_vendidos": json.dumps(productos_data),
            },
        )
        venta_id = cursor.lastrowid

        registrar_log(usuario, "registrar_venta", {"venta_id": venta_id, "total": total, "pagado": pagado})

    return {
        "id": venta_id,
        "total": total,
        "pagado": pagado,
        "fecha": fecha,
        "productos_vendidos": productos_data,
    }


def editar_venta_extra(
    sale_id: str,
    observaciones: Optional[str] = None,
    vendedor: Optional[str] = None,
    telefono_vendedor: Optional[str] = None,
    chofer: Optional[str] = None,
    chapa: Optional[str] = None,
    usuario: Optional[str] = None,
):
    """Editar campos adicionales de una venta."""
    with get_connection() as conn:
        update_query = """
            UPDATE ventas
            SET observaciones = COALESCE(:observaciones, observaciones),
                vendedor = COALESCE(:vendedor, vendedor),
                telefono_vendedor = COALESCE(:telefono_vendedor, telefono_vendedor),
                chofer = COALESCE(:chofer, chofer),
                chapa = COALESCE(:chapa, chapa)
            WHERE id = :id
        """
        conn.execute(
            update_query,
            {
                "id": sale_id,
                "observaciones": observaciones,
                "vendedor": vendedor,
                "telefono_vendedor": telefono_vendedor,
                "chofer": chofer,
                "chapa": chapa,
            },
        )
        updated = conn.execute("SELECT * FROM ventas WHERE id = ?", (sale_id,)).fetchone()

        if updated:
            registrar_log(usuario or "sistema", "editar_venta_extra", dict(updated))
            return dict(updated)

    return None


def list_sales():
    """Listar todas las ventas, normalizando fechas y productos."""
    query = "SELECT * FROM ventas ORDER BY fecha DESC"
    with get_connection() as conn:
        resultados = conn.execute(query).fetchall()

    ventas_list = []
    for row in resultados:
        r_dict = dict(row)
        r_dict["productos_vendidos"] = _deserialize_productos(r_dict.get("productos_vendidos"))
        r_dict["fecha"] = _normalize_fecha(r_dict.get("fecha"))
        ventas_list.append(r_dict)

    return ventas_list


def get_sale(sale_id: str) -> Optional[Dict]:
    """Obtener una venta por su ID."""
    query = "SELECT * FROM ventas WHERE id = ?"
    with get_connection() as conn:
        result = conn.execute(query, (sale_id,)).fetchone()
    if result:
        r_dict = dict(result)
        r_dict["fecha"] = _normalize_fecha(r_dict.get("fecha"))
        r_dict["productos_vendidos"] = _deserialize_productos(r_dict.get("productos_vendidos"))
        return r_dict
    return None


def delete_sale(sale_id: str, usuario: Optional[str] = None) -> bool:
    """Eliminar una venta por su ID."""
    sale = get_sale(sale_id)
    if not sale:
        return False

    with get_connection() as conn:
        conn.execute("DELETE FROM ventas WHERE id = ?", (sale_id,))

    registrar_log(usuario or "sistema", "eliminar_venta", {"venta_id": sale_id, "venta": sale})
    return True


def listar_ventas_dict():
    """Crear un diccionario de ventas para selección rápida."""
    ventas = list_sales()
    return {f"ID {v['id']} - Cliente {v['cliente_id']} - Total ${v['total']}": v for v in ventas}


def generar_factura_pdf(
    venta,
    cliente,
    productos_vendidos,
    gestor_info=None,
    logo_path: Optional[str] = None,
):
    """
    Generar una factura PDF con los detalles de la venta.

    venta: dict con info de la venta
    cliente: dict con info del cliente
    productos_vendidos: lista de dicts {nombre, cantidad, precio_unitario}
    gestor_info: dict opcional con datos del vendedor/chofer
    logo_path: ruta local a logo de la empresa
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    line_height = 15

    if not logo_path:
        logo_path = str(resolve_asset_path("assets/logo.png"))

    logo = None
    if os.path.exists(logo_path):
        try:
            logo = ImageReader(logo_path)
        except Exception as exc:
            print(f"No se pudo cargar el logo: {exc}")

    def dibujar_factura(y_offset=0):
        nonlocal c

        if logo:
            c.drawImage(logo, 40, height - 85 - y_offset, width=80, height=70, preserveAspectRatio=True)

        c.setFont("Helvetica-Bold", 14)
        c.drawString(130, height - 50 - y_offset, "Omar Galíndez Ramirez. CI: 85082506984")
        c.setFont("Helvetica", 10)
        c.drawString(130, height - 65 - y_offset, f"Factura N°: {venta.get('numero', venta.get('id',''))}")
        c.drawString(130, height - 80 - y_offset, f"Fecha: {venta.get('fecha','')}")

        col1_x = 40
        col2_x = 320
        row_y = height - 110 - y_offset

        cliente_nombre = cliente.get("nombre") or ""
        cliente_ci = cliente.get("ci") or ""
        cliente_chapa = cliente.get("chapa") or ""
        cliente_direccion = cliente.get("direccion") or ""
        cliente_telefono = cliente.get("telefono") or ""

        c.setFont("Helvetica-Bold", 10)
        c.drawString(col1_x, row_y, "Cliente:")
        c.setFont("Helvetica", 10)
        c.drawString(col1_x + 60, row_y, cliente_nombre)
        c.drawString(col1_x, row_y - line_height, f"CI: {cliente_ci}")
        c.drawString(col1_x, row_y - line_height * 2, f"Chapa: {cliente_chapa}")
        c.drawString(col1_x, row_y - line_height * 3, f"Dirección: {cliente_direccion}")
        c.drawString(col1_x, row_y - line_height * 4, f"Teléfono: {cliente_telefono}")

        c.setFont("Helvetica-Bold", 10)
        c.drawString(col2_x, row_y, "Gestor:")
        c.setFont("Helvetica", 10)

        if gestor_info:
            c.drawString(col2_x + 50, row_y, gestor_info.get("vendedor", ""))
            c.drawString(col2_x, row_y - line_height, f"Tel: {gestor_info.get('telefono_vendedor','')}")
            c.drawString(col2_x, row_y - line_height * 2, f"Chofer: {gestor_info.get('chofer','')}")
            c.drawString(col2_x, row_y - line_height * 3, f"Chapa: {gestor_info.get('chapa','')}")
        else:
            c.drawString(col2_x + 50, row_y, "")

        table_data = [["Producto", "Cantidad", "Precio U.", "Subtotal"]]
        total = 0
        for p in productos_vendidos:
            subtotal = float(p.get("cantidad", 0)) * float(p.get("precio_unitario", 0))
            total += subtotal
            table_data.append(
                [
                    p.get("nombre", ""),
                    f"{p.get('cantidad', 0)}",
                    f"${p.get('precio_unitario', 0):.2f}",
                    f"${subtotal:.2f}",
                ]
            )

        table = Table(table_data, colWidths=[200, 70, 80, 80])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ]
            )
        )

        table.wrapOn(c, width, height)
        table.drawOn(c, col1_x, row_y - 240)

        c.setFont("Helvetica-Bold", 12)
        c.drawString(col2_x, row_y - 260, f"Total: ${total:.2f}")

    dibujar_factura(0)
    dibujar_factura(400)

    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer

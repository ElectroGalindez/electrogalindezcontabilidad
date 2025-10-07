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

from io import BytesIO
import pandas as pd

def generar_factura_excel(venta, cliente, productos_vendidos, gestor_info=None):
    """
    Genera factura profesional en Excel lista para descargar o imprimir.
    - venta: dict con info de la venta (número, fecha, total, pagos, observaciones)
    - cliente: dict con info del cliente (nombre, carnet, identidad, chapa)
    - productos_vendidos: lista de dicts {nombre, cantidad, precio_unitario, importe}
    - gestor_info: dict opcional con datos del vendedor/gestor/chofer
    """
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book

        # Crear hoja de factura
        sheet_name = "Factura"
        worksheet = workbook.add_worksheet(sheet_name)
        writer.sheets[sheet_name] = worksheet

        # Formatos
        bold = workbook.add_format({'bold': True})
        center = workbook.add_format({'align': 'center'})
        currency = workbook.add_format({'num_format': '$#,##0.00'})
        border = workbook.add_format({'border': 1})
        wrap = workbook.add_format({'text_wrap': True, 'border':1})

        # Ajuste ancho columnas
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 25)

        # Función para dibujar una factura (media hoja)
        def dibujar_factura(fila_inicio):
            row = fila_inicio
            # Encabezado empresa
            worksheet.write(row, 0, "ElectroGalíndez S.A.", bold)
            worksheet.write(row, 3, f"Número: {venta.get('numero','')}")
            row += 1
            worksheet.write(row, 0, f"Fecha: {venta.get('fecha','')}")
            worksheet.write(row, 3, f"Proveedor: {venta.get('proveedor','')}")
            row += 2

            # Cliente
            worksheet.write(row, 0, "Cliente:", bold)
            worksheet.write(row, 1, cliente.get("nombre",""))
            worksheet.write(row, 3, "Carnet/ID:", bold)
            worksheet.write(row, 4, cliente.get("carnet",""))
            row += 1
            worksheet.write(row, 0, "Identidad:", bold)
            worksheet.write(row, 1, cliente.get("identidad",""))
            worksheet.write(row, 3, "Chapa:", bold)
            worksheet.write(row, 4, cliente.get("chapa",""))
            row += 2

            # Productos
            df_prod = pd.DataFrame(productos_vendidos)
            df_prod['importe'] = df_prod['cantidad'] * df_prod['precio_unitario']
            df_prod.to_excel(writer, sheet_name=sheet_name, startrow=row, startcol=0, index=False)
            row += len(df_prod) + 3

            # Totales y pagos
            worksheet.write(row, 0, "Total:", bold)
            worksheet.write(row, 1, venta.get("total",""), currency)
            row += 1
            worksheet.write(row, 0, "Pagado:", bold)
            worksheet.write(row, 1, venta.get("pagado",""), currency)
            worksheet.write(row, 3, "Saldo Pendiente:", bold)
            worksheet.write(row, 4, venta.get("saldo",""), currency)
            row += 2

            # Desglose pago
            worksheet.write(row, 0, "Desglose de Pago:", bold)
            row +=1
            for metodo, monto in venta.get("desglose_pago", {}).items():
                worksheet.write(row, 0, metodo)
                worksheet.write(row, 1, monto, currency)
                row +=1

            # Observaciones
            worksheet.write(row, 0, "Observaciones:", bold)
            worksheet.write(row, 1, venta.get("observaciones",""), wrap)
            row += 2

            # Vendedor / Chofer / Firma
            if gestor_info:
                worksheet.write(row, 0, "Vendedor:", bold)
                worksheet.write(row, 1, gestor_info.get("vendedor",""))
                worksheet.write(row, 3, "Chofer:", bold)
                worksheet.write(row, 4, gestor_info.get("chofer",""))
                row +=2
                worksheet.write(row, 0, "Firma Cliente:", bold)
                worksheet.write(row, 1, "")
                worksheet.write(row, 3, "Firma Vendedor:", bold)
                worksheet.write(row, 4, "")

        # Dibujar dos facturas por hoja
        dibujar_factura(0)     # Primera mitad
        dibujar_factura(30)    # Segunda mitad (ajustar según altura)

    output.seek(0)
    return output.getvalue()

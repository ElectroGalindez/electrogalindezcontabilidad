# backend/reportes.py
from sqlalchemy import text
from backend.db import engine
import datetime
import pandas as pd
from collections import Counter
from .logs import registrar_log

# =============================
# Ventas Diarias
# =============================
def ventas_diarias(fecha=None, actor=None):
    """
    Devuelve todas las ventas de una fecha específica con productos incluidos.
    """
    if fecha is None:
        fecha = datetime.date.today()
    elif isinstance(fecha, str):
        fecha = datetime.datetime.strptime(fecha, "%Y-%m-%d").date()

    query = text("""
        SELECT v.id AS venta_id, v.cliente_id, v.total, v.pagado, v.tipo_pago, v.fecha,
               p.nombre AS producto, p.cantidad, p.precio_unitario, p.subtotal
        FROM ventas v
        LEFT JOIN productos_vendidos p ON p.venta_id = v.id
        WHERE DATE(v.fecha) = :fecha
        ORDER BY v.fecha
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"fecha": fecha})
        ventas = [dict(r) for r in result]

    registrar_log(
        usuario=actor or "sistema",
        accion="reporte_ventas_diarias",
        detalles={"fecha": str(fecha), "total_registros": len(ventas)}
    )
    return ventas

# =============================
# Ventas Mensuales
# =============================
def ventas_mensuales(mes, anio, actor=None):
    """
    Devuelve todas las ventas de un mes específico.
    """
    query = text("""
        SELECT v.id AS venta_id, v.cliente_id, v.total, v.pagado, v.tipo_pago, v.fecha,
               p.nombre AS producto, p.cantidad, p.precio_unitario, p.subtotal
        FROM ventas v
        LEFT JOIN productos_vendidos p ON p.venta_id = v.id
        WHERE EXTRACT(MONTH FROM v.fecha) = :mes AND EXTRACT(YEAR FROM v.fecha) = :anio
        ORDER BY v.fecha
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"mes": mes, "anio": anio})
        ventas = [dict(r) for r in result]

    registrar_log(
        usuario=actor or "sistema",
        accion="reporte_ventas_mensuales",
        detalles={"mes": mes, "anio": anio, "total_registros": len(ventas)}
    )
    return ventas

# =============================
# Productos Más Vendidos
# =============================
def productos_mas_vendidos(actor=None, top_n=None):
    """
    Devuelve los productos más vendidos de todas las ventas.
    Si top_n está definido, limita el resultado.
    """
    query = text("""
        SELECT nombre, SUM(cantidad) AS total_vendido
        FROM productos_vendidos
        GROUP BY nombre
        ORDER BY total_vendido DESC
    """)
    with engine.connect() as conn:
        result = conn.execute(query)
        productos = [dict(r) for r in result]

    if top_n:
        productos = productos[:top_n]

    registrar_log(
        usuario=actor or "sistema",
        accion="reporte_productos_mas_vendidos",
        detalles={"total_productos": len(productos)}
    )
    return productos

# =============================
# Deudas de Clientes
# =============================
def deudas_clientes(actor=None):
    """
    Devuelve un DataFrame con todas las deudas pendientes.
    """
    query = text("""
        SELECT d.id AS deuda_id, d.cliente_id, c.nombre AS cliente_nombre,
               d.monto_total, d.estado, d.fecha
        FROM deudas d
        LEFT JOIN clientes c ON c.id = d.cliente_id
        ORDER BY d.fecha
    """)
    with engine.connect() as conn:
        result = conn.execute(query)
        deudas = [dict(r) for r in result]

    df = pd.DataFrame(deudas)
    registrar_log(
        usuario=actor or "sistema",
        accion="reporte_deudas_clientes",
        detalles={"total_registros": len(df)}
    )
    return df

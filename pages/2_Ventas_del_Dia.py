import streamlit as st
import pandas as pd
from io import BytesIO
from backend import ventas, clientes, productos 
import numpy as np

st.set_page_config(page_title="Ventas del Día", layout="wide")
st.title("🛒 Reporte de Ventas del Día")

# ---------------------------
# Filtrar por fecha
# ---------------------------
st.subheader("📅 Filtrar por fecha")
fecha_inicio = st.date_input("Fecha inicio", value=pd.Timestamp.today())
fecha_fin = st.date_input("Fecha fin", value=pd.Timestamp.today())
if fecha_inicio > fecha_fin:
    st.error("La fecha de inicio no puede ser mayor que la fecha final")
    st.stop()

# ---------------------------
# Obtener ventas y clientes
# ---------------------------
ventas_data = ventas.list_sales()
clientes_data = {c["id"]: c for c in clientes.list_clients()}

# ---------------------------
# Función para crear filas
# ---------------------------
def generar_filas(v):
    fecha_venta = pd.to_datetime(v.get("fecha", pd.Timestamp.now()))
    cliente = clientes_data.get(v.get("cliente_id"), {"nombre": "Desconocido", "telefono": ""})
    estado = "Pagada" if v.get("pagado", 0.0) >= v.get("total", 0.0) else "Pendiente"
    productos_vendidos = v.get("productos_vendidos") or []

    filas = []
    if not productos_vendidos:
        filas.append({
            "ID Venta": v.get("id", ""),
            "Fecha": fecha_venta,
            "Cliente": cliente.get("nombre"),
            "Teléfono": cliente.get("telefono", ""),
            "Producto": "",
            "Cantidad": 0,
            "Precio Unitario": 0.0,
            "Subtotal": 0.0,
            "Total Venta": v.get("total", 0.0),
            "Pagado": v.get("pagado", 0.0),
            "Saldo Pendiente": max(v.get("total", 0.0) - v.get("pagado", 0.0), 0.0),
            "Estado": estado
        })
    else:
        for p in productos_vendidos:
            filas.append({
                "ID Venta": v.get("id", ""),
                "Fecha": fecha_venta,
                "Cliente": cliente.get("nombre"),
                "Teléfono": cliente.get("telefono", ""),
                "Producto": p.get("nombre", ""),
                "Cantidad": p.get("cantidad", 0),
                "Precio Unitario": p.get("precio_unitario", 0.0),
                "Subtotal": p.get("subtotal", 0.0),
                "Total Venta": v.get("total", 0.0),
                "Pagado": v.get("pagado", 0.0),
                "Saldo Pendiente": max(v.get("total", 0.0) - v.get("pagado", 0.0), 0.0),
                "Estado": estado
            })
    return filas

# ---------------------------
# Crear DataFrame con ventas del rango seleccionado
# ---------------------------
rows = [
    fila
    for v in ventas_data
    if fecha_inicio <= pd.to_datetime(v.get("fecha", pd.Timestamp.now())).date() <= fecha_fin
    for fila in generar_filas(v)
]

if not rows:
    st.info("No hay ventas registradas en este rango de fechas.")
    st.stop()

df_ventas = pd.DataFrame(rows)

# ---------------------------
# Asegurar columnas clave
# ---------------------------
cols_principales = [
    "ID Venta", "Fecha", "Cliente", "Teléfono", "Producto",
    "Cantidad", "Precio Unitario", "Total Venta", "Pagado", "Saldo Pendiente", "Estado"
]
for col in cols_principales:
    if col not in df_ventas.columns:
        df_ventas[col] = ""

# ---------------------------
# Limpieza y formato
# ---------------------------
df_ventas["Fecha"] = pd.to_datetime(df_ventas["Fecha"], errors="coerce")
df_ventas = df_ventas.sort_values("Fecha", ascending=False)

# Redondear y formatear números
for c in ["Cantidad", "Precio Unitario", "Total Venta", "Pagado", "Saldo Pendiente"]:
    if c in df_ventas.columns:
        df_ventas[c] = pd.to_numeric(df_ventas[c], errors="coerce").fillna(0).round(2)

# Aplicar formato visual
df_ventas_display = df_ventas.copy()
df_ventas_display["Precio Unitario"] = df_ventas_display["Precio Unitario"].apply(lambda x: f"${x:,.2f}")
df_ventas_display["Total Venta"] = df_ventas_display["Total Venta"].apply(lambda x: f"${x:,.2f}")
df_ventas_display["Pagado"] = df_ventas_display["Pagado"].apply(lambda x: f"${x:,.2f}")
df_ventas_display["Saldo Pendiente"] = df_ventas_display["Saldo Pendiente"].apply(lambda x: f"${x:,.2f}")

# ---------------------------
# Mostrar todas las ventas
# ---------------------------
st.subheader("📋 Todas las Ventas")
st.dataframe(df_ventas_display[cols_principales], use_container_width=True, hide_index=True)

# ---------------------------
# Ventas Pagadas
# ---------------------------
st.subheader("✅ Ventas Pagadas")
pagadas = df_ventas[df_ventas["Estado"].str.lower() == "pagada"]
if not pagadas.empty:
    total_pagadas = pagadas["Pagado"].sum()
    st.metric("💵 Total Ventas Pagadas", f"${total_pagadas:,.2f}")
    st.dataframe(df_ventas_display[df_ventas_display["Estado"].str.lower() == "pagada"], use_container_width=True, hide_index=True)
else:
    st.info("No hay ventas pagadas en este rango.")

# ---------------------------
# Ventas con Deuda
# ---------------------------
st.subheader("⚠️ Ventas con Deuda")
pendientes = df_ventas[df_ventas["Estado"].str.lower() == "pendiente"]
if not pendientes.empty:
    total_pendiente = pendientes["Saldo Pendiente"].sum()
    st.metric("💰 Total Pendiente", f"${total_pendiente:,.2f}")
    st.dataframe(df_ventas_display[df_ventas_display["Estado"].str.lower() == "pendiente"], use_container_width=True, hide_index=True)
else:
    st.info("No hay ventas pendientes en este rango.")

# ---------------------------
# Métricas Generales
# ---------------------------
st.subheader("📊 Métricas Generales")
st.metric("Total ventas", f"{df_ventas['ID Venta'].nunique()}")
st.metric("Productos vendidos", f"{df_ventas['Cantidad'].sum():,.0f}")
st.metric("Total pagado", f"${df_ventas['Pagado'].sum():,.2f}")
st.metric("Deuda total", f"${df_ventas['Saldo Pendiente'].sum():,.2f}")

import pandas as pd
import streamlit as st

st.subheader("🏆 Productos Más Vendidos (según precio del inventario)")

# ---------------------------
# Cargar tabla de productos y renombrar columnas
productos_data = productos.list_products()  # tu función para obtener productos
df_productos = pd.DataFrame(productos_data).rename(columns={"nombre": "Producto", "precio": "Precio"})

# Convertir Precio a float (de Decimal a float)
df_productos["Precio"] = df_productos["Precio"].apply(float)

# ---------------------------
# Agrupar ventas por producto
productos_vendidos = df_ventas.groupby("Producto")["Cantidad"].sum().reset_index()

# ---------------------------
# Unir con tabla de productos para obtener precio actual
productos_vendidos = productos_vendidos.merge(
    df_productos[["Producto", "Precio"]],
    on="Producto",
    how="left"
)

# ---------------------------
# Asegurarse de que Cantidad sea float
productos_vendidos["Cantidad"] = productos_vendidos["Cantidad"].astype(float)

# ---------------------------
# Calcular total vendido
productos_vendidos["Total Vendido"] = productos_vendidos["Cantidad"] * productos_vendidos["Precio"]

# ---------------------------
# Ordenar por cantidad vendida
productos_vendidos = productos_vendidos.sort_values("Cantidad", ascending=False)

# ---------------------------
# Formatear valores monetarios
productos_vendidos["Precio"] = productos_vendidos["Precio"].apply(lambda x: f"${x:,.2f}")
productos_vendidos["Total Vendido"] = productos_vendidos["Total Vendido"].apply(lambda x: f"${x:,.2f}")

# ---------------------------
# Mostrar tabla
st.dataframe(productos_vendidos, use_container_width=True, hide_index=True)

#boton de descarga de excel de cantidad de productos vendidos solo de las columnas Producto y Cantidad
def descargar_excel_productos_vendidos(df: pd.DataFrame, nombre_archivo: str):
    """
    Descarga un DataFrame como Excel, quitando la columna 'Subtotal' y formateando fechas.
    """
    df_export = df[["Producto", "Cantidad"]].copy()
    
    # 🔹 Crear buffer Excel
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_export.to_excel(writer, index=False, sheet_name="Productos Vendidos")
    
    # 🔹 Botón de descarga
    st.download_button(
        label=f"💾 Descargar {nombre_archivo}",
        data=buffer.getvalue(),
        file_name=f"{nombre_archivo}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
descargar_excel_productos_vendidos(productos_vendidos, f"productos_vendidos_{fecha_inicio}_{fecha_fin}")
# ---------------------------
# Botones de descarga Excel
# ---------------------------

def descargar_excel(df: pd.DataFrame, nombre_archivo: str):
    """
    Descarga un DataFrame como Excel, quitando la columna 'Subtotal' y formateando fechas.
    """
    df_export = df.copy()
    
    # 🔹 Eliminar columna 'Subtotal' si existe
    if "Subtotal" in df_export.columns:
        df_export.drop(columns=["Subtotal"], inplace=True)
    
    # 🔹 Formatear todas las columnas datetime
    for col in df_export.columns:
        if np.issubdtype(df_export[col].dtype, np.datetime64):
            df_export[col] = df_export[col].dt.strftime("%Y-%m-%d %H:%M:%S")
    
    # 🔹 Crear buffer Excel
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_export.to_excel(writer, index=False, sheet_name="Reporte")
    
    # 🔹 Botón de descarga
    st.download_button(
        label=f"💾 Descargar {nombre_archivo}",
        data=buffer.getvalue(),
        file_name=f"{nombre_archivo}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.markdown("---")
descargar_excel(df_ventas, f"ventas_completas_{fecha_inicio}_{fecha_fin}")
if not pagadas.empty:
    descargar_excel(pagadas, f"ventas_pagadas_{fecha_inicio}_{fecha_fin}")
if not pendientes.empty:
    descargar_excel(pendientes, f"ventas_pendientes_{fecha_inicio}_{fecha_fin}")

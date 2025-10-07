import streamlit as st
import pandas as pd
from io import BytesIO
from backend import ventas, clientes

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
# Crear DataFrame
# ---------------------------
rows = [fila for v in ventas_data if fecha_inicio <= pd.to_datetime(v.get("fecha", pd.Timestamp.now())).date() <= fecha_fin for fila in generar_filas(v)]
if not rows:
    st.info("No hay ventas registradas en este rango de fechas.")
    st.stop()

df_ventas = pd.DataFrame(rows)

# Asegurar columnas esperadas
expected_cols = ["ID Venta","Fecha","Cliente","Teléfono","Producto","Cantidad","Precio Unitario",
                 "Subtotal","Total Venta","Pagado","Saldo Pendiente","Estado"]
for col in expected_cols:
    if col not in df_ventas.columns:
        df_ventas[col] = 0 if df_ventas.empty else ""

df_ventas["Fecha_dt"] = df_ventas["Fecha"]
df_ventas["Fecha_str"] = df_ventas["Fecha_dt"].dt.date
df_ventas["Hora"] = df_ventas["Fecha_dt"].dt.strftime("%H:%M:%S")
df_ventas = df_ventas.sort_values("Fecha_dt")

# ---------------------------
# Mostrar todas las ventas
# ---------------------------
st.subheader("📋 Todas las ventas")
st.dataframe(df_ventas.drop(columns=["Fecha_dt","Fecha_str"]), use_container_width=True)

# ---------------------------
# Ventas Pagadas
# ---------------------------
st.subheader("✅ Ventas Pagadas")
pagadas = df_ventas[df_ventas["Estado"] == "Pagada"]
if not pagadas.empty:
    st.dataframe(pagadas, use_container_width=True)
    st.metric("Total ventas pagadas", f"${pagadas['Pagado'].sum():,.2f}")
else:
    st.info("No hay ventas pagadas en este rango.")

# ---------------------------
# Ventas con Deuda
# ---------------------------
st.subheader("⚠️ Ventas con Deuda")
pendientes = df_ventas[df_ventas["Estado"] == "Pendiente"]
if not pendientes.empty:
    st.dataframe(pendientes, use_container_width=True)
    st.metric("Total pendiente", f"${pendientes['Subtotal'].sum():,.2f}")
else:
    st.info("No hay ventas pendientes en este rango.")

# ---------------------------
# Métricas Generales
# ---------------------------
st.subheader("📊 Métricas Generales")
st.metric("Total ventas", f"{df_ventas['ID Venta'].nunique()}")
st.metric("Productos vendidos", f"{df_ventas['Cantidad'].sum():,.0f}")
st.metric("Ingresos totales", f"${df_ventas['Subtotal'].sum():,.2f}")
st.metric("Total pagado", f"${df_ventas['Pagado'].sum():,.2f}")
st.metric("Deuda total", f"${df_ventas['Saldo Pendiente'].sum():,.2f}")

# ---------------------------
# Botones de descarga Excel
# ---------------------------
def descargar_excel(df, nombre_archivo):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Reporte")
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

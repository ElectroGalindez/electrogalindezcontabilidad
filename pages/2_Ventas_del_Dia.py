# frontend/pages/2_Ventas_del_Dia.py
import streamlit as st
import pandas as pd
from io import BytesIO
from backend import ventas, clientes

st.set_page_config(page_title="Ventas del Día", layout="wide")
st.title("🛒 Ventas del Día")

# ---------------------------
# Filtro por fecha
# ---------------------------
st.subheader("📅 Filtrar por fecha")
fecha_inicio = st.date_input("Fecha inicio", pd.Timestamp.today())
fecha_fin = st.date_input("Fecha fin", pd.Timestamp.today())

if fecha_inicio > fecha_fin:
    st.error("La fecha de inicio no puede ser mayor que la fecha final")
    st.stop()

# ---------------------------
# Obtener ventas
# ---------------------------
ventas_data = ventas.list_sales()
clientes_data = {c["id"]: c for c in clientes.list_clients()}

# Filtrar por rango de fechas
ventas_filtradas = [
    v for v in ventas_data
    if fecha_inicio <= pd.to_datetime(v.get("fecha")).date() <= fecha_fin
]

if not ventas_filtradas:
    st.info("No hay ventas registradas en este rango de fechas.")
    st.stop()

# ---------------------------
# Preparar DataFrame de detalle
# ---------------------------
rows = []
for v in ventas_filtradas:
    cliente = clientes_data.get(v["cliente_id"], {"nombre": "Desconocido", "telefono": ""})
    estado = "Pagada" if v.get("pagado", 0.0) >= v.get("total", 0.0) else "Pendiente"
    for p in v.get("productos_vendidos", []):
        subtotal = p.get("cantidad", 0) * p.get("precio_unitario", 0.0)
        rows.append({
            "ID Venta": v["id"],
            "Fecha": pd.to_datetime(v["fecha"]),
            "Cliente": cliente.get("nombre"),
            "Teléfono": cliente.get("telefono"),
            "Producto": p.get("nombre"),
            "Cantidad": p.get("cantidad"),
            "Precio Unitario": p.get("precio_unitario"),
            "Subtotal": subtotal,
            "Total Venta": v.get("total"),
            "Pagado": v.get("pagado"),
            "Saldo Pendiente": max(v.get("total", 0.0) - v.get("pagado", 0.0), 0.0),
            "Estado": estado
        })

df_ventas = pd.DataFrame(rows)
df_ventas["Hora"] = df_ventas["Fecha"].dt.strftime("%H:%M:%S")
df_ventas["Fecha_str"] = df_ventas["Fecha"].dt.date

# ---------------------------
# Mostrar ventas
# ---------------------------
st.subheader("📋 Ventas del Rango Seleccionado")
st.dataframe(df_ventas.sort_values(["Fecha", "ID Venta"]), use_container_width=True)

# ---------------------------
# Totales
# ---------------------------
total_ingresos = df_ventas["Subtotal"].sum()
total_pagado = df_ventas["Pagado"].sum()
total_deuda = df_ventas["Saldo Pendiente"].sum()

st.metric("💰 Total Ingresos", f"${total_ingresos:,.2f}")
st.metric("✅ Total Pagado", f"${total_pagado:,.2f}")
st.metric("⚠️ Total Deuda", f"${total_deuda:,.2f}")

# ---------------------------
# Descargar Excel
# ---------------------------
buffer = BytesIO()
with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    df_ventas.to_excel(writer, index=False, sheet_name="Ventas del Día")
st.download_button(
    label="💾 Descargar Excel",
    data=buffer.getvalue(),
    file_name=f"ventas_{fecha_inicio}_{fecha_fin}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

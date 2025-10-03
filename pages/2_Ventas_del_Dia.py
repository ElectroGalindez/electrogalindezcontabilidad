# frontend/pages/2_Ventas_del_Dia.py
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
# Obtener ventas
# ---------------------------
ventas_data = ventas.list_sales()
clientes_data = {c["id"]: c for c in clientes.list_clients()}

# Filtrar ventas por rango de fechas
ventas_filtradas = [
    v for v in ventas_data
    if fecha_inicio <= pd.to_datetime(v.get("fecha", pd.Timestamp.now())).date() <= fecha_fin
]

if not ventas_filtradas:
    st.info("No hay ventas registradas en este rango de fechas.")
    st.stop()

# ---------------------------
# Preparar DataFrame de ventas detalladas
# ---------------------------
rows = []
for v in ventas_filtradas:
    cliente = clientes_data.get(v.get("cliente_id"), {"nombre": "Desconocido", "telefono": ""})
    estado = "Pagada" if v.get("pagado", 0.0) >= v.get("total", 0.0) else "Pendiente"

    for p in v.get("productos_vendidos", []):
        rows.append({
            "ID Venta": v.get("id", ""),
            "Fecha": pd.to_datetime(v.get("fecha", pd.Timestamp.now())),
            "Cliente": cliente.get("nombre", "Desconocido"),
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

df_ventas = pd.DataFrame(rows)
df_ventas = df_ventas.sort_values("Fecha")
df_ventas["Fecha_dt"] = df_ventas["Fecha"]
df_ventas["Fecha_str"] = df_ventas["Fecha_dt"].dt.date
df_ventas["Hora"] = df_ventas["Fecha_dt"].dt.strftime("%H:%M:%S")

# ---------------------------
# Ventas Pagadas
# ---------------------------
st.subheader("✅ Ventas Pagadas")
pagadas = df_ventas[df_ventas["Estado"] == "Pagada"]
if not pagadas.empty:
    st.dataframe(pagadas, use_container_width=True)
    total_pagadas = pagadas["Subtotal"].sum()
    st.metric("Total ventas pagadas", f"${total_pagadas:,.2f}")

    # Descargar ventas pagadas
    buffer_pagadas = BytesIO()
    with pd.ExcelWriter(buffer_pagadas, engine='xlsxwriter') as writer:
        pagadas.to_excel(writer, index=False, sheet_name="Ventas Pagadas")
    st.download_button(
        label="💾 Descargar Ventas Pagadas",
        data=buffer_pagadas.getvalue(),
        file_name=f"ventas_pagadas_{fecha_inicio}_{fecha_fin}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("No hay ventas pagadas en este rango.")

# ---------------------------
# Ventas con Deuda
# ---------------------------
st.subheader("⚠️ Ventas con Deuda")
pendientes = df_ventas[df_ventas["Estado"] == "Pendiente"]
if not pendientes.empty:
    st.dataframe(pendientes, use_container_width=True)
    total_pendientes = pendientes["Subtotal"].sum()
    st.metric("Total pendiente", f"${total_pendientes:,.2f}")

    # Descargar ventas pendientes
    buffer_pendientes = BytesIO()
    with pd.ExcelWriter(buffer_pendientes, engine='xlsxwriter') as writer:
        pendientes.to_excel(writer, index=False, sheet_name="Ventas Pendientes")
    st.download_button(
        label="💾 Descargar Ventas Pendientes",
        data=buffer_pendientes.getvalue(),
        file_name=f"ventas_pendientes_{fecha_inicio}_{fecha_fin}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("No hay ventas pendientes en este rango.")

# ---------------------------
# Resumen Diario Detallado
# ---------------------------
st.subheader("📊 Resumen Diario Detallado")
if not df_ventas.empty:
    # Agrupar por fecha
    resumen_diario = df_ventas.groupby("Fecha_str").agg(
        ventas_totales=("ID Venta", "nunique"),
        productos_vendidos=("Cantidad", "sum"),
        total_ingresos=("Subtotal", "sum"),
        total_pagado=("Pagado", "sum"),
        total_deuda=("Saldo Pendiente", "sum")
    ).reset_index()

    st.markdown("### Resumen por Día")
    st.dataframe(resumen_diario, use_container_width=True)

    # Detalle ventas por día
    for fecha, grupo in df_ventas.groupby("Fecha_str"):
        st.markdown(f"### 📅 Detalle de Ventas - {fecha}")
        st.dataframe(grupo.drop(columns=["Fecha_dt", "Fecha_str"]), use_container_width=True)

    # Descargar resumen diario con detalle
    buffer_resumen = BytesIO()
    with pd.ExcelWriter(buffer_resumen, engine='xlsxwriter') as writer:
        # Guardar resumen
        resumen_diario.to_excel(writer, index=False, sheet_name="Resumen Diario")
        # Guardar detalle por fecha
        for fecha, grupo in df_ventas.groupby("Fecha_str"):
            grupo_excel = grupo.drop(columns=["Fecha_dt", "Fecha_str"])
            grupo_excel.to_excel(writer, index=False, sheet_name=str(fecha))
            # Dar formato a Fecha y Hora
            worksheet = writer.sheets[str(fecha)]
            workbook = writer.book
            date_fmt = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss'})
            worksheet.set_column('B:B', 20, date_fmt)  # columna Fecha y Hora
    st.download_button(
        label="💾 Descargar Resumen Diario",
        data=buffer_resumen.getvalue(),
        file_name=f"resumen_diario_{fecha_inicio}_{fecha_fin}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

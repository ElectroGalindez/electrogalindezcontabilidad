# ElectroGalíndez.py
import streamlit as st
import pandas as pd
import plotly.express as px
from backend import productos, clientes, ventas, deudas, usuarios

# -------------------------
# Configuración página
# -------------------------
st.set_page_config(page_title="ElectroGalíndez - Contabilidad", layout="wide")
st.title("📊 ElectroGalíndez - Sistema Contable")

# -------------------------
# Sesión usuario
# -------------------------
if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión.")
    st.stop()

st.info(f"Sesión iniciada: {st.session_state.usuario['username']} ({st.session_state.usuario['rol']})")

# -------------------------
# Registrar log de acceso
# -------------------------
try:
    usuarios.registrar_log(st.session_state.usuario['username'], "ver_dashboard", "Accedió al dashboard principal")
except:
    pass  # evitar error si log falla

# -------------------------
# Cargar datos desde Neon
# -------------------------
productos_data = productos.list_products() or []
clientes_data = clientes.list_clients() or []
ventas_data = ventas.list_sales() or []
deudas_data = deudas.list_debts() or []

# -------------------------
# Convertir a DataFrames
# -------------------------
df_productos = pd.DataFrame(productos_data)
df_clientes = pd.DataFrame(clientes_data)
df_ventas = pd.DataFrame(ventas_data)
df_deudas = pd.DataFrame(deudas_data)

# Asegurar columnas
if not df_ventas.empty and "fecha" in df_ventas.columns:
    df_ventas["fecha"] = pd.to_datetime(df_ventas["fecha"])

# -------------------------
# KPIs - fila 1
# -------------------------
col1, col2, col3 = st.columns(3)

ventas_hoy = df_ventas[df_ventas["fecha"].dt.date == pd.Timestamp.today().date()] if not df_ventas.empty else pd.DataFrame()
total_dia = ventas_hoy["total"].sum() if not ventas_hoy.empty else 0.0
col1.metric("💰 Ventas hoy", f"${total_dia:,.2f}", "✅ Hoy" if total_dia > 0 else "⚠️ Sin ventas")

total_mes = df_ventas[df_ventas["fecha"].dt.month == pd.Timestamp.today().month]["total"].sum() if not df_ventas.empty else 0.0
col2.metric("📈 Ventas mes actual", f"${total_mes:,.2f}", "✅ En curso" if total_mes > 0 else "⚠️ Sin ventas")

total_deuda = df_deudas[df_deudas["estado"]=="pendiente"]["monto_total"].sum() if not df_deudas.empty else 0.0
col3.metric("💳 Deudas pendientes", f"${total_deuda:,.2f}", "⚠️ Revisar" if total_deuda>0 else "✅ Sin deudas")

# -------------------------
# KPIs - fila 2
# -------------------------
col1, col2, col3 = st.columns(3)
col1.metric("🛒 Nº Ventas hoy", len(ventas_hoy))
ticket_promedio = ventas_hoy["total"].mean() if not ventas_hoy.empty else 0.0
col2.metric("🧾 Ticket promedio (hoy)", f"${ticket_promedio:,.2f}")
total_ventas = df_ventas["total"].sum() if not df_ventas.empty else 0.0
pct_deuda = (total_deuda/total_ventas*100) if total_ventas>0 else 0
col3.metric("💳 % Deuda sobre ventas", f"{pct_deuda:.1f}%")

# -------------------------
# KPIs - fila 3
# -------------------------
col1, col2, col3 = st.columns(3)
stock_bajo = df_productos[df_productos["cantidad"]<=5].shape[0] if not df_productos.empty else 0
col1.metric("📦 Total Productos", df_productos.shape[0] if not df_productos.empty else 0, f"⚠️ {stock_bajo} stock bajo" if stock_bajo else "✅ Stock OK")
col2.metric("👥 Clientes registrados", df_clientes.shape[0] if not df_clientes.empty else 0)
clientes_con_deuda = df_clientes[df_clientes.get("deuda_total", 0)>0].shape[0] if not df_clientes.empty else 0
col3.metric("👥 Clientes con deuda", clientes_con_deuda)

st.write("Ventas:", df_ventas)
st.write("Productos:", df_productos)
st.write("Clientes:", df_clientes)

# -------------------------
# Gráficos
# -------------------------
st.subheader("📊 Gráficos de Ventas y Deudas")

# 1️⃣ Ventas últimos 7 días
if not df_ventas.empty:
    ultimos_7 = df_ventas[df_ventas["fecha"] >= pd.Timestamp.today() - pd.Timedelta(days=7)]
    if not ultimos_7.empty:
        df_diaria = ultimos_7.groupby(ultimos_7["fecha"].dt.date)["total"].sum().reset_index()
        fig1 = px.bar(df_diaria, x="fecha", y="total", title="Ventas últimos 7 días", text_auto=True)
        st.plotly_chart(fig1, use_container_width=True)

# 2️⃣ Ventas mensuales
if not df_ventas.empty:
    df_mensuales = df_ventas.groupby(df_ventas["fecha"].dt.to_period("M"))["total"].sum().reset_index()
    df_mensuales["fecha"] = df_mensuales["fecha"].astype(str)
    if not df_mensuales.empty:
        fig2 = px.bar(df_mensuales, x="fecha", y="total", title="Ventas Mensuales", text_auto=True)
        st.plotly_chart(fig2, use_container_width=True)

# 3️⃣ Ventas por categoría
if not df_ventas.empty and not df_productos.empty:
    merged = []
    for v in ventas_data:
        productos_vendidos = v.get("productos_vendidos") or []
        if isinstance(productos_vendidos, dict):
            productos_vendidos = [productos_vendidos]
        for it in productos_vendidos:
            pid = it.get("id_producto")
            cantidad = it.get("cantidad",0)
            prod = next((p for p in productos_data if p["id"]==pid), None)
            if prod:
                merged.append({"categoria": prod.get("categoria_id","Sin Categoría"), "cantidad": cantidad})
    df_cat = pd.DataFrame(merged)
    if not df_cat.empty:
        df_cat_agg = df_cat.groupby("categoria")["cantidad"].sum().reset_index()
        fig3 = px.pie(df_cat_agg, names="categoria", values="cantidad", title="Ventas por Categoría")
        st.plotly_chart(fig3, use_container_width=True)

# 4️⃣ Top 5 clientes
if not df_ventas.empty and not df_clientes.empty:
    top_clientes = df_ventas.groupby("cliente_id")["total"].sum().reset_index()
    if not top_clientes.empty:
        top_clientes = top_clientes.sort_values(by="total", ascending=False).head(5)
        top_clientes["cliente"] = top_clientes["cliente_id"].apply(
            lambda cid: next((c["nombre"] for c in clientes_data if c["id"]==cid), str(cid))
        )
        fig4 = px.bar(top_clientes, x="cliente", y="total", title="Top 5 Clientes por Ventas", text_auto=True)
        st.plotly_chart(fig4, use_container_width=True)

# 5️⃣ Top 5 productos
if not df_ventas.empty and not df_productos.empty:
    prod_count = {}
    for v in ventas_data:
        productos_vendidos = v.get("productos_vendidos") or []
        if isinstance(productos_vendidos, dict):
            productos_vendidos = [productos_vendidos]
        for it in productos_vendidos:
            pid = it.get("id_producto")
            cantidad = it.get("cantidad",0)
            prod_count[pid] = prod_count.get(pid,0)+cantidad
    df_prod = pd.DataFrame([
        {"producto": next((p["nombre"] for p in productos_data if p["id"]==pid), str(pid)), "cantidad": cant}
        for pid, cant in prod_count.items()
    ])
    if not df_prod.empty:
        df_prod = df_prod.sort_values("cantidad", ascending=False).head(5)
        fig5 = px.bar(df_prod, x="producto", y="cantidad", title="Top 5 Productos más vendidos", text_auto=True)
        st.plotly_chart(fig5, use_container_width=True)

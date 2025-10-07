# ElectroGalíndez.py
import streamlit as st
import pandas as pd
import plotly.express as px
from backend import productos, clientes, ventas, deudas, usuarios

# =====================================================
# CONFIGURACIÓN INICIAL
# =====================================================
st.set_page_config(page_title="ElectroGalíndez - Sistema Contable", layout="wide")
st.title("📊 ElectroGalíndez - Panel General")

# -------------------------
# SESIÓN DE USUARIO
# -------------------------
if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("⚠️ Debes iniciar sesión para acceder al panel.")
    st.stop()

usuario = st.session_state.usuario
st.markdown(f"👤 **Usuario:** `{usuario['username']}` | Rol: `{usuario['rol']}`")

# Log de acceso
try:
    usuarios.registrar_log(usuario["username"], "ver_dashboard", "Acceso al panel principal")
except Exception:
    pass

# =====================================================
# CARGA DE DATOS
# =====================================================
@st.cache_data(ttl=60)
def cargar_datos():
    return (
        productos.list_products() or [],
        clientes.list_clients() or [],
        ventas.list_sales() or [],
        deudas.list_debts() or []
    )

productos_data, clientes_data, ventas_data, deudas_data = cargar_datos()

df_productos = pd.DataFrame(productos_data)
df_clientes = pd.DataFrame(clientes_data)
df_ventas = pd.DataFrame(ventas_data)
df_deudas = pd.DataFrame(deudas_data)

if not df_ventas.empty and "fecha" in df_ventas.columns:
    df_ventas["fecha"] = pd.to_datetime(df_ventas["fecha"])
else:
    df_ventas["fecha"] = pd.Timestamp.now()

# =====================================================
# MÉTRICAS PRINCIPALES (KPI)
# =====================================================
ventas_hoy = df_ventas[df_ventas["fecha"].dt.date == pd.Timestamp.today().date()]
total_hoy = ventas_hoy["total"].sum() if not ventas_hoy.empty else 0.0
total_mes = df_ventas[df_ventas["fecha"].dt.month == pd.Timestamp.today().month]["total"].sum() if not df_ventas.empty else 0.0
total_deuda = df_deudas[df_deudas["estado"] == "pendiente"]["monto_total"].sum() if not df_deudas.empty else 0.0

col1, col2, col3 = st.columns(3)
col1.metric("💰 Ventas del Día", f"${total_hoy:,.2f}", "✅ Activo" if total_hoy > 0 else "⚠️ Sin ventas")
col2.metric("📅 Ventas del Mes", f"${total_mes:,.2f}")
col3.metric("💳 Deuda Pendiente", f"${total_deuda:,.2f}", "⚠️ Revisar" if total_deuda > 0 else "✅ Sin deudas")

# =====================================================
# KPIs SECUNDARIOS
# =====================================================
if not df_ventas.empty:
    df_ventas["total"] = df_ventas["total"].astype(float)
    df_ventas["saldo"] = df_ventas["saldo"].astype(float)

    ventas_hoy["total"] = ventas_hoy["total"].astype(float)

    ticket_promedio = ventas_hoy["total"].mean() if not ventas_hoy.empty else 0.0
    pct_deuda = (df_ventas["saldo"].sum() / df_ventas["total"].sum() * 100) if df_ventas["total"].sum() > 0 else 0.0

    col1, col2, col3 = st.columns(3)
    col1.metric("🛒 Nº Ventas Hoy", len(ventas_hoy))
    col2.metric("🧾 Ticket Promedio", f"${ticket_promedio:,.2f}")
    col3.metric("💸 % Deuda / Ventas", f"{pct_deuda:.1f}%")

# =====================================================
# INVENTARIO Y CLIENTES
# =====================================================
col1, col2, col3 = st.columns(3)
stock_bajo = df_productos[df_productos["cantidad"] <= 5].shape[0] if not df_productos.empty else 0
col1.metric("📦 Productos Registrados", len(df_productos), f"⚠️ {stock_bajo} con stock bajo" if stock_bajo else "✅ Stock OK")
col2.metric("👥 Clientes Totales", len(df_clientes))
clientes_con_deuda = df_clientes[df_clientes.get("deuda_total", 0) > 0].shape[0] if not df_clientes.empty else 0
col3.metric("💳 Clientes con Deuda", clientes_con_deuda)

# =====================================================
# VISUALIZACIONES
# =====================================================
st.markdown("---")
st.subheader("📈 Reportes Visuales")

# 🔹 Ventas últimos 7 días
if not df_ventas.empty:
    ultimos_7 = df_ventas[df_ventas["fecha"] >= pd.Timestamp.today() - pd.Timedelta(days=7)]
    df_diaria = ultimos_7.groupby(ultimos_7["fecha"].dt.date)["total"].sum().reset_index()
    fig1 = px.bar(df_diaria, x="fecha", y="total", title="📅 Ventas Últimos 7 Días",
                  color="total", text_auto=".2s", color_continuous_scale="Blues")
    st.plotly_chart(fig1, use_container_width=True)

# 🔹 Ventas mensuales
if not df_ventas.empty:
    df_mensual = df_ventas.groupby(df_ventas["fecha"].dt.to_period("M"))["total"].sum().reset_index()
    df_mensual["fecha"] = df_mensual["fecha"].astype(str)
    fig2 = px.line(df_mensual, x="fecha", y="total", title="📊 Tendencia de Ventas Mensuales",
                   markers=True, line_shape="spline")
    st.plotly_chart(fig2, use_container_width=True)

# 🔹 Top 5 productos
if not df_ventas.empty and not df_productos.empty:
    conteo = {}
    for v in ventas_data:
        for p in v.get("productos_vendidos", []):
            pid = p.get("id_producto")
            cant = p.get("cantidad", 0)
            conteo[pid] = conteo.get(pid, 0) + cant
    df_top_prod = pd.DataFrame([
        {"Producto": next((x["nombre"] for x in productos_data if x["id"] == pid), f"ID {pid}"), "Cantidad": cant}
        for pid, cant in conteo.items()
    ]).sort_values("Cantidad", ascending=False).head(5)
    fig3 = px.bar(df_top_prod, x="Producto", y="Cantidad", title="🏆 Top 5 Productos Más Vendidos",
                  text_auto=True, color="Cantidad", color_continuous_scale="Viridis")
    st.plotly_chart(fig3, use_container_width=True)

# 🔹 Top 5 clientes
if not df_ventas.empty:
    top_clientes = df_ventas.groupby("cliente_id")["total"].sum().reset_index()
    top_clientes["Cliente"] = top_clientes["cliente_id"].apply(
        lambda cid: next((c["nombre"] for c in clientes_data if c["id"] == cid), str(cid))
    )
    df_top_clientes = top_clientes.sort_values("total", ascending=False).head(5)
    fig4 = px.bar(df_top_clientes, x="Cliente", y="total", title="💎 Top 5 Clientes por Ventas",
                  text_auto=".2s", color="total", color_continuous_scale="Teal")
    st.plotly_chart(fig4, use_container_width=True)

# 🔹 Ventas por categoría (si aplica)
if not df_productos.empty:
    merged = []
    for v in ventas_data:
        for item in v.get("productos_vendidos", []):
            pid = item.get("id_producto")
            cantidad = item.get("cantidad", 0)
            prod = next((p for p in productos_data if p["id"] == pid), None)
            if prod:
                merged.append({"Categoría": prod.get("categoria_id", "Sin Categoría"), "Cantidad": cantidad})
    df_cat = pd.DataFrame(merged)
    if not df_cat.empty:
        df_cat_agg = df_cat.groupby("Categoría")["Cantidad"].sum().reset_index()
        fig5 = px.pie(df_cat_agg, names="Categoría", values="Cantidad", title="🧩 Ventas por Categoría")
        st.plotly_chart(fig5, use_container_width=True)

st.markdown("---")
st.caption("© 2025 ElectroGalíndez | Sistema Contable desarrollado con Streamlit & Neon PostgreSQL")

import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

# ---------------------------
# Ajuste del path para backend
# ---------------------------
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# ---------------------------
# Importar backend
# ---------------------------
from backend import productos, clientes, ventas, deudas

# ---------------------------
# Configuración de la app
# ---------------------------
st.set_page_config(
    page_title="ElectroGalíndez - Sistema Contable",
    page_icon="💰",
    layout="wide"
)

st.title("📊 ElectroGalíndez - Sistema de Contabilidad")
st.markdown("""
Bienvenido al sistema contable de **ElectroGalíndez**.  
Aquí tienes un resumen rápido de la situación actual de tu negocio.
""")

if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()



# =========================
# Cargar datos
# =========================
productos_data = productos.list_products()
clientes_data = clientes.list_clients()
ventas_data = ventas.list_sales()
deudas_data = deudas.list_debts()

# =========================
# KPIs generales
# =========================
import streamlit as st
import pandas as pd

st.subheader("📌 Resumen General")

# Columnas para el resumen
col1, col2, col3, col4, col5 = st.columns(5)

# Total productos y alerta stock bajo
total_productos = len(productos_data)
stock_bajo = sum(1 for p in productos_data if p["cantidad"] <= 5)
stock_alerta = f"⚠️ {stock_bajo} con stock bajo" if stock_bajo else "✅ Stock OK"
col1.metric(
    label="📦 Total Productos",
    value=total_productos,
    delta=stock_alerta
)

# Total clientes
total_clientes = len(clientes_data)
col2.metric(
    label="👥 Clientes registrados",
    value=total_clientes
)

# Ventas del día
if ventas_data:
    df_ventas = pd.DataFrame(ventas_data)
    df_ventas["fecha"] = pd.to_datetime(df_ventas["fecha"])
    total_dia = df_ventas[df_ventas["fecha"].dt.date == pd.Timestamp.today().date()]["total"].sum()
else:
    total_dia = 0.0
col3.metric(
    label="💰 Ventas hoy",
    value=f"${total_dia:,.2f}",
    delta="✅ Hoy" if total_dia > 0 else "⚠️ Sin ventas"
)

# Ventas del mes
if ventas_data:
    total_mes = df_ventas[df_ventas["fecha"].dt.month == pd.Timestamp.today().month]["total"].sum()
else:
    total_mes = 0.0
col4.metric(
    label="📈 Ventas mes actual",
    value=f"${total_mes:,.2f}",
    delta="✅ En curso" if total_mes > 0 else "⚠️ Sin ventas"
)

# Deudas pendientes
df_deudas = pd.DataFrame([d for d in deudas_data if d["estado"] == "pendiente"]) if deudas_data else pd.DataFrame()
total_deuda = df_deudas["monto"].sum() if not df_deudas.empty else 0.0
col5.metric(
    label="💳 Deudas pendientes",
    value=f"${total_deuda:,.2f}",
    delta="⚠️ Revisar" if total_deuda > 0 else "✅ Sin deudas"
)

# Opcional: mini gráficos de tendencia (ventas últimos 7 días)
st.markdown("### 📊 Tendencia de ventas últimos 7 días")
if ventas_data:
    ultimos_7 = df_ventas[df_ventas["fecha"] >= (pd.Timestamp.today() - pd.Timedelta(days=7))]
    df_diaria = ultimos_7.groupby(ultimos_7["fecha"].dt.date)["total"].sum().reset_index()
    st.bar_chart(df_diaria.rename(columns={"fecha": "index"}).set_index("index")["total"])
else:
    st.info("No hay ventas registradas en los últimos 7 días")

# =========================
# Producto más vendid
# =========================
st.subheader("🏆 Producto más vendido")
col1, col2, col3, col4 = st.columns(4)

# Productos más vendidos
if ventas_data:
    productos_count = {}
    for v in ventas_data:
        for it in v["productos_vendidos"]:
            pid = it["id_producto"]
            productos_count[pid] = productos_count.get(pid, 0) + it["cantidad"]
    if productos_count:
        top_prod_id = max(productos_count, key=productos_count.get)
        top_prod = next((p["nombre"] for p in productos_data if p["id"] == top_prod_id), top_prod_id)
        col1.metric("Producto más vendido", top_prod, f"{productos_count[top_prod_id]} unidades")
    else:
        col1.metric("Producto más vendido", "-", "-")
else:
    col1.metric("Producto más vendido", "-", "-")

# Cliente con mayor deuda
if clientes_data and not df_deudas.empty:
    deudas_por_cliente = df_deudas.groupby("cliente_id")["monto"].sum()
    cliente_mayor_id = deudas_por_cliente.idxmax()
    cliente_mayor = next((c["nombre"] for c in clientes_data if c["id"] == cliente_mayor_id), cliente_mayor_id)
    monto = deudas_por_cliente.max()
    col2.metric("Cliente mayor deuda", cliente_mayor, f"${monto:,.2f}")
else:
    col2.metric("Cliente mayor deuda", "-", "-")

# Venta más alta del mes
if ventas_data:
    df_ventas_mes = df_ventas[df_ventas["fecha"].dt.month == pd.Timestamp.today().month]
    if not df_ventas_mes.empty:
        max_venta = df_ventas_mes["total"].max()
        col3.metric("Venta más alta", f"${max_venta:,.2f}")
    else:
        col3.metric("Venta más alta", "-", "-")
else:
    col3.metric("Venta más alta", "-", "-")

# Promedio de venta por cliente
if ventas_data and clientes_data:
    df_ventas_cliente = df_ventas.groupby("cliente_id")["total"].sum()
    if not df_ventas_cliente.empty:
        promedio = df_ventas_cliente.mean()
        col4.metric("Promedio venta/cliente", f"${promedio:,.2f}")
    else:
        col4.metric("Promedio venta/cliente", "-", "-")
else:
    col4.metric("Promedio venta/cliente", "-", "-")

# =========================
# Gráficos miniatura
# =========================
st.subheader("📊 Gráficos Rápidos")

if ventas_data:
    # Ventas mensuales
    df_mensuales = df_ventas.groupby(df_ventas["fecha"].dt.to_period("M"))["total"].sum().reset_index()
    df_mensuales["fecha"] = df_mensuales["fecha"].astype(str)
    fig1 = px.bar(df_mensuales, x="fecha", y="total", title="Ventas Mensuales")
    st.plotly_chart(fig1, use_container_width=True)

    # Porcentaje de ventas por categoría
    cat_count = {}
    for v in ventas_data:
        for it in v["productos_vendidos"]:
            prod = next((p for p in productos_data if p["id"] == it["id_producto"]), None)
            if prod:
                cat = prod.get("categoria", "Sin Categoría")
                cat_count[cat] = cat_count.get(cat, 0) + it["cantidad"]
    df_cat = pd.DataFrame([{"categoria": k, "cantidad": v} for k, v in cat_count.items()])
    if not df_cat.empty:
        fig2 = px.pie(df_cat, names="categoria", values="cantidad", title="Ventas por Categoría")
        st.plotly_chart(fig2, use_container_width=True)


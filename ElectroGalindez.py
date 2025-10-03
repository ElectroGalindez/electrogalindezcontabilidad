import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ---------------------------
# Ajuste del path para backend
# ---------------------------
BASE_DIR = Path(__file__).resolve().parent  # ElectroGalindez.py está en la raíz
DATA_DIR = BASE_DIR / "data"
BACKUPS_DIR = BASE_DIR / "backups"

# ---------------------------
# Importar backend
# ---------------------------
from backend import productos, clientes, ventas, deudas

# =========================
# Función utilitaria
# =========================
def get_monto_deuda(d: dict) -> float:
    """Devuelve el monto de una deuda, manejando claves diferentes."""
    return d.get("monto", d.get("monto_total", 0.0))

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
# KPIs - Fila 1
# =========================
col1, col2, col3 = st.columns(3)

# Ventas del día
if ventas_data:
    df_ventas = pd.DataFrame(ventas_data)
    df_ventas["fecha"] = pd.to_datetime(df_ventas["fecha"])
    ventas_hoy = df_ventas[df_ventas["fecha"].dt.date == pd.Timestamp.today().date()]
    total_dia = ventas_hoy["total"].sum()
else:
    ventas_hoy = pd.DataFrame()
    total_dia = 0.0
col1.metric("💰 Ventas hoy", f"${total_dia:,.2f}", "✅ Hoy" if total_dia > 0 else "⚠️ Sin ventas")

# Ventas del mes
total_mes = df_ventas[df_ventas["fecha"].dt.month == pd.Timestamp.today().month]["total"].sum() if ventas_data else 0.0
col2.metric("📈 Ventas mes actual", f"${total_mes:,.2f}", "✅ En curso" if total_mes > 0 else "⚠️ Sin ventas")

# Deudas pendientes
total_deuda = sum(d.get("monto", 0) for d in deudas_data if d.get("estado") == "pendiente") if deudas_data else 0.0
col3.metric("💳 Deudas pendientes", f"${total_deuda:,.2f}", "⚠️ Revisar" if total_deuda > 0 else "✅ Sin deudas")


# =========================
# KPIs - Fila 2
# =========================
col1, col2, col3 = st.columns(3)

# Nº ventas hoy
num_ventas_hoy = len(ventas_hoy) if not ventas_hoy.empty else 0
col1.metric("🛒 Nº Ventas hoy", num_ventas_hoy)

# Ticket promedio hoy
ticket_promedio_hoy = ventas_hoy["total"].mean() if not ventas_hoy.empty else 0
col2.metric("🧾 Ticket promedio (hoy)", f"${ticket_promedio_hoy:,.2f}")

# % de deuda sobre ventas
total_ventas = df_ventas["total"].sum() if ventas_data else 0
pct_deuda = (total_deuda / total_ventas * 100) if total_ventas > 0 else 0
col3.metric("💳 % Deuda sobre ventas", f"{pct_deuda:.1f}%")


# =========================
# KPIs - Fila 3
# =========================
col1, col2, col3 = st.columns(3)

# Total productos y stock bajo
total_productos = len(productos_data)
stock_bajo = sum(1 for p in productos_data if p["cantidad"] <= 5)
col1.metric("📦 Total Productos", total_productos, f"⚠️ {stock_bajo} stock bajo" if stock_bajo else "✅ Stock OK")

# Total clientes
total_clientes = len(clientes_data)
col2.metric("👥 Clientes registrados", total_clientes)

# Clientes con deuda
clientes_con_deuda = len([c for c in clientes_data if c.get("deuda_total", 0) > 0])
col3.metric("👥 Clientes con deuda", clientes_con_deuda)


# =========================
# Gráficos interactivos
# =========================
st.subheader("📊 Gráficos de Ventas y Deudas")

# 1. Tendencia últimos 7 días
if ventas_data:
    ultimos_7 = df_ventas[df_ventas["fecha"] >= (pd.Timestamp.today() - pd.Timedelta(days=7))]
    df_diaria = ultimos_7.groupby(ultimos_7["fecha"].dt.date)["total"].sum().reset_index()
    fig1 = px.bar(df_diaria, x="fecha", y="total", title="Ventas últimos 7 días")
    st.plotly_chart(fig1, use_container_width=True)

# 2. Ventas mensuales
if ventas_data:
    df_mensuales = df_ventas.groupby(df_ventas["fecha"].dt.to_period("M"))["total"].sum().reset_index()
    df_mensuales["fecha"] = df_mensuales["fecha"].astype(str)
    fig2 = px.bar(df_mensuales, x="fecha", y="total", title="Ventas Mensuales", text_auto=True)
    st.plotly_chart(fig2, use_container_width=True)

# 3. Ventas por categoría
cat_count = {}
for v in ventas_data:
    for it in v["productos_vendidos"]:
        prod = next((p for p in productos_data if p["id"] == it["id_producto"]), None)
        if prod:
            cat = prod.get("categoria", "Sin Categoría")
            cat_count[cat] = cat_count.get(cat, 0) + it["cantidad"]
df_cat = pd.DataFrame([{"categoria": k, "cantidad": v} for k, v in cat_count.items()])
if not df_cat.empty:
    fig3 = px.pie(df_cat, names="categoria", values="cantidad", title="Ventas por Categoría")
    st.plotly_chart(fig3, use_container_width=True)

# 4. Top 5 clientes
if ventas_data:
    top_clientes = df_ventas.groupby("cliente_id")["total"].sum().reset_index()
    top_clientes = top_clientes.sort_values(by="total", ascending=False).head(5)
    top_clientes["cliente"] = top_clientes["cliente_id"].apply(
        lambda cid: next((c["nombre"] for c in clientes_data if c["id"] == cid), str(cid))
    )
    fig4 = px.bar(top_clientes, x="cliente", y="total", title="Top 5 Clientes por Ventas", text_auto=True)
    st.plotly_chart(fig4, use_container_width=True)

# 5. Top 5 productos
productos_count = {}
for v in ventas_data:
    for it in v["productos_vendidos"]:
        productos_count[it["id_producto"]] = productos_count.get(it["id_producto"], 0) + it["cantidad"]
df_prod = pd.DataFrame([
    {"producto": next((p["nombre"] for p in productos_data if p["id"] == pid), str(pid)),
     "cantidad": cant}
    for pid, cant in productos_count.items()
]).sort_values(by="cantidad", ascending=False).head(5)
if not df_prod.empty:
    fig5 = px.bar(df_prod, x="producto", y="cantidad", title="Top 5 Productos más vendidos", text_auto=True)
    st.plotly_chart(fig5, use_container_width=True)


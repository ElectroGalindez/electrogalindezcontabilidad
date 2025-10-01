
# frontend/pages/4_Reportes.py
import streamlit as st
import pandas as pd
from backend import ventas, productos, deudas, clientes
import plotly.express as px

st.title("📈 Reportes y Análisis")

if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()


# ===========================
# DATOS BASE
# ===========================
ventas_data = ventas.list_sales()
productos_data = {p["id"]: p for p in productos.list_products()}
deudas_data = deudas.list_debts()
clientes_data = clientes.list_clients()

# ===========================
# MÉTRICAS PRINCIPALES
# ===========================
col1, col2, col3 = st.columns(3)

total_ventas = sum(v["total"] for v in ventas_data) if ventas_data else 0
col1.metric("💵 Total Ventas", f"${total_ventas:,.2f}")

clientes_con_deuda = len([c for c in clientes_data if c.get("deuda_total", 0) > 0])
col2.metric("👥 Clientes con deuda", clientes_con_deuda)

total_deuda = sum(d["monto"] for d in deudas_data if d["estado"] == "pendiente") if deudas_data else 0
col3.metric("💰 Total Deudas Pendientes", f"${total_deuda:,.2f}")

# ===========================
# VENTAS: DIARIAS Y MENSUALES
# ===========================
st.subheader("📅 Evolución de Ventas")

if ventas_data:
    df_ventas = pd.DataFrame(ventas_data)
    df_ventas["fecha"] = pd.to_datetime(df_ventas["fecha"])
    
    # Ventas diarias
    df_diarias = df_ventas.groupby("fecha")["total"].sum().reset_index()
    fig1 = px.bar(df_diarias, x="fecha", y="total",
                  title="Ventas diarias", text_auto=True)
    st.plotly_chart(fig1, use_container_width=True)

    # Ventas mensuales
    df_ventas["mes"] = df_ventas["fecha"].dt.to_period("M").astype(str)
    df_mensuales = df_ventas.groupby("mes")["total"].sum().reset_index()
    fig2 = px.line(df_mensuales, x="mes", y="total", markers=True,
                   title="Ventas mensuales")
    st.plotly_chart(fig2, use_container_width=True)

else:
    st.info("⚠️ No hay ventas registradas aún.")

# ===========================
# PRODUCTOS MÁS VENDIDOS
# ===========================
st.subheader("🏆 Productos más vendidos")

if ventas_data:
    productos_count = {}
    for v in ventas_data:
        for it in v["productos_vendidos"]:
            pid = it["id_producto"]
            productos_count[pid] = productos_count.get(pid, 0) + it["cantidad"]

    df_top = pd.DataFrame([
        {"Producto": productos_data.get(pid, {}).get("nombre", pid), "Cantidad vendida": qty}
        for pid, qty in productos_count.items()
    ])
    df_top = df_top.sort_values("Cantidad vendida", ascending=False)

    fig3 = px.bar(df_top.head(10), x="Producto", y="Cantidad vendida",
                  title="Top 10 productos más vendidos", text_auto=True)
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("⚠️ No hay ventas para analizar productos.")

# ===========================
# DEUDAS PENDIENTES
# ===========================
st.subheader("💳 Deudas Pendientes")

if deudas_data:
    df_deudas = pd.DataFrame([d for d in deudas_data if d["estado"] == "pendiente"])
    
    if not df_deudas.empty:
        # Mostrar tabla con cliente asociado
        df_deudas["Cliente"] = df_deudas["cliente_id"].apply(
            lambda cid: next((c["nombre"] for c in clientes_data if c["id"] == cid), cid)
        )
        df_deudas = df_deudas[["id", "Cliente", "monto", "estado", "fecha"]]

        st.dataframe(df_deudas, use_container_width=True)

        fig4 = px.pie(df_deudas, values="monto", names="Cliente",
                      title="Distribución de deudas por cliente")
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.success("✅ No hay deudas pendientes.")
else:
    st.info("⚠️ No hay deudas registradas.")

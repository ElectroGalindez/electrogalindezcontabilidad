"""Streamlit dashboard for ElectroGalindez."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from backend import clientes, deudas, productos, usuarios, ventas


def _require_user() -> dict:
    """Return the logged-in user or stop execution."""
    usuario = st.session_state.get("usuario")
    if not usuario:
        st.warning("⚠️ Debes iniciar sesión para acceder al panel.")
        st.stop()
    return usuario


@st.cache_data(ttl=60)
def _load_data() -> dict:
    """Load core datasets with caching to reduce DB reads."""
    return {
        "productos": productos.list_products() or [],
        "clientes": clientes.list_clients() or [],
        "ventas": ventas.list_sales() or [],
        "deudas": deudas.list_debts() or [],
    }


def _prepare_frames(data: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build pandas DataFrames for the dashboard charts."""
    df_prod = pd.DataFrame(data["productos"])
    df_cli = pd.DataFrame(data["clientes"])
    df_ven = pd.DataFrame(data["ventas"])
    df_deu = pd.DataFrame(data["deudas"])

    if not df_ven.empty and "fecha" in df_ven.columns:
        df_ven["fecha"] = pd.to_datetime(df_ven["fecha"])
    else:
        df_ven["fecha"] = pd.Timestamp.now()

    return df_prod, df_cli, df_ven, df_deu


def _render_primary_kpis(df_ven: pd.DataFrame, df_deu: pd.DataFrame) -> None:
    """Render primary KPI metrics."""
    hoy = pd.Timestamp.today().date()

    ventas_hoy = df_ven[df_ven["fecha"].dt.date == hoy]
    total_hoy = ventas_hoy["total"].sum() if not ventas_hoy.empty else 0

    total_mes = (
        df_ven[df_ven["fecha"].dt.month == pd.Timestamp.today().month]["total"].sum()
        if not df_ven.empty
        else 0
    )

    total_deuda = df_deu[df_deu["estado"] == "pendiente"]["monto_total"].sum() if not df_deu.empty else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Ventas Hoy", f"${total_hoy:,.2f}")
    col2.metric("📅 Ventas Mes", f"${total_mes:,.2f}")
    col3.metric("💳 Deudas Pendientes", f"${total_deuda:,.2f}")


def _render_secondary_kpis(df_ven: pd.DataFrame) -> None:
    """Render secondary KPI metrics."""
    if df_ven.empty:
        return

    df_ven["total"] = df_ven["total"].astype(float)
    df_ven["saldo"] = df_ven["saldo"].astype(float)

    hoy = pd.Timestamp.today().date()
    ventas_hoy = df_ven[df_ven["fecha"].dt.date == hoy]
    ticket_prom = ventas_hoy["total"].mean() if not ventas_hoy.empty else 0
    porc_deuda = (df_ven["saldo"].sum() / df_ven["total"].sum() * 100) if df_ven["total"].sum() > 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("🛒 Ventas Hoy", len(ventas_hoy))
    c2.metric("🧾 Ticket Promedio", f"${ticket_prom:,.2f}")
    c3.metric("💸 % Deuda / Ventas", f"{porc_deuda:.1f}%")


def _render_inventory_metrics(df_prod: pd.DataFrame, df_cli: pd.DataFrame) -> None:
    """Render inventory and customer metrics."""
    c1, c2, c3 = st.columns(3)

    stock_bajo = df_prod[df_prod["cantidad"] <= 5].shape[0] if not df_prod.empty else 0
    c1.metric("📦 Productos", len(df_prod), f"⚠️ {stock_bajo} con stock bajo" if stock_bajo else "OK")
    c2.metric("👥 Clientes", len(df_cli))

    cli_con_deuda = df_cli[df_cli.get("deuda_total", 0) > 0].shape[0] if not df_cli.empty else 0
    c3.metric("💳 Clientes con Deuda", cli_con_deuda)


def _render_charts(data: dict, df_ven: pd.DataFrame) -> None:
    """Render dashboard charts."""
    if df_ven.empty:
        return

    ult_7 = df_ven[df_ven["fecha"] >= pd.Timestamp.today() - pd.Timedelta(days=7)]
    df7 = ult_7.groupby(ult_7["fecha"].dt.date)["total"].sum().reset_index()
    if not df7.empty:
        fig1 = px.bar(df7, x="fecha", y="total", title="📅 Ventas Últimos 7 Días")
        st.plotly_chart(fig1, use_container_width=True)

    dfm = df_ven.groupby(df_ven["fecha"].dt.to_period("M"))["total"].sum().reset_index()
    dfm["fecha"] = dfm["fecha"].astype(str)
    if not dfm.empty:
        fig2 = px.line(dfm, x="fecha", y="total", markers=True, title="📊 Ventas Mensuales")
        st.plotly_chart(fig2, use_container_width=True)

    detalles = []
    for venta in data["ventas"]:
        detalles += venta.get("productos_vendidos", [])

    if detalles:
        df_det = pd.DataFrame(detalles)
        df_det_group = df_det.groupby("id_producto")["cantidad"].sum().reset_index()

        df_det_group["Producto"] = df_det_group["id_producto"].apply(
            lambda x: next((p["nombre"] for p in data["productos"] if p["id"] == x), f"ID {x}")
        )

        df_top = df_det_group.sort_values("cantidad", ascending=False).head(5)
        fig3 = px.bar(df_top, x="Producto", y="cantidad", title="🏆 Top 5 Productos")
        st.plotly_chart(fig3, use_container_width=True)

    dfcli = df_ven.groupby("cliente_id")["total"].sum().reset_index()
    dfcli["Cliente"] = dfcli["cliente_id"].apply(
        lambda x: next((c["nombre"] for c in data["clientes"] if c["id"] == x), f"ID {x}")
    )
    dfcli = dfcli.sort_values("total", ascending=False).head(5)

    fig4 = px.bar(dfcli, x="Cliente", y="total", title="💎 Top 5 Clientes")
    st.plotly_chart(fig4, use_container_width=True)


def render() -> None:
    """Render the main Streamlit dashboard."""
    st.set_page_config(page_title="ElectroGalíndez - Dashboard", layout="wide")
    st.title("📊 ElectroGalíndez - Panel General")

    usuario = _require_user()
    st.markdown(f"👤 **Usuario:** `{usuario['username']}` | Rol: `{usuario['rol']}`")

    try:
        usuarios.registrar_log(usuario["username"], "ver_dashboard", "Acceso al panel principal")
    except Exception:
        pass

    data = _load_data()
    df_prod, df_cli, df_ven, df_deu = _prepare_frames(data)

    _render_primary_kpis(df_ven, df_deu)
    _render_secondary_kpis(df_ven)
    _render_inventory_metrics(df_prod, df_cli)

    st.markdown("---")
    st.subheader("📈 Reportes Visuales")
    _render_charts(data, df_ven)

    st.markdown("---")
    st.caption("© 2025 ElectroGalíndez | Dashboard optimizado para alto rendimiento.")

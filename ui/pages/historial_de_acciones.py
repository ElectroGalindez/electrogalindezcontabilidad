import streamlit as st
import pandas as pd
from io import BytesIO


def render() -> None:
    st.set_page_config(page_title="Historial de Acciones", layout="wide")
    st.title("📜 Historial de Acciones")

    if "usuario" not in st.session_state or st.session_state.usuario is None:
        st.warning("Debes iniciar sesión para acceder a esta página.")
        st.stop()
    if st.session_state.usuario["rol"] != "admin":
        st.error("Solo usuarios con rol admin pueden acceder.")
        st.stop()

    @st.cache_data
    def cargar_historial():
        data = {
            "Fecha": pd.date_range("2025-01-01", periods=15, freq="D"),
            "Usuario": ["admin", "omar", "maria", "admin", "omar"] * 3,
            "Módulo": ["Clientes", "Deudas", "Pagos", "Usuarios", "Reportes"] * 3,
            "Acción": [
                "Creó cliente", "Actualizó deuda", "Registró pago",
                "Eliminó usuario", "Generó reporte"
            ] * 3,
            "Detalle": [
                "Cliente Juan Pérez", "Deuda #45", "Pago de $50",
                "Usuario Pedro", "Reporte de ventas"
            ] * 3
        }
        df = pd.DataFrame(data)
        df["Fecha"] = pd.to_datetime(df["Fecha"]).dt.strftime("%Y-%m-%d %H:%M:%S")
        return df

    df_historial = cargar_historial()

    col1, col2, col3 = st.columns(3)

    usuarios = ["Todos"] + sorted(df_historial["Usuario"].unique().tolist())
    modulos = ["Todos"] + sorted(df_historial["Módulo"].unique().tolist())

    usuario_filtro = col1.selectbox("👤 Usuario", usuarios)
    modulo_filtro = col2.selectbox("📦 Módulo", modulos)
    fecha_min = col3.date_input("📅 Desde", pd.to_datetime(df_historial["Fecha"]).min())
    fecha_max = col3.date_input("📅 Hasta", pd.to_datetime(df_historial["Fecha"]).max())

    df_filtrado = df_historial.copy()

    df_filtrado["Fecha_dt"] = pd.to_datetime(df_filtrado["Fecha"])
    df_filtrado = df_filtrado[
        (df_filtrado["Fecha_dt"].dt.date >= fecha_min) &
        (df_filtrado["Fecha_dt"].dt.date <= fecha_max)
    ]

    if usuario_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Usuario"] == usuario_filtro]

    if modulo_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Módulo"] == modulo_filtro]

    df_filtrado.drop(columns="Fecha_dt", inplace=True)

    st.subheader("📋 Resultados del historial")
    st.dataframe(df_filtrado, use_container_width=True)

    def exportar_excel(df):
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Historial")
        buffer.seek(0)
        return buffer

    excel_buffer = exportar_excel(df_filtrado)
    st.download_button(
        label="⬇️ Descargar historial filtrado (Excel)",
        data=excel_buffer,
        file_name="historial_acciones.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.caption(f"Mostrando {len(df_filtrado)} registros filtrados de {len(df_historial)} totales.")
    st.markdown("---")

# pages/7_Logs.py
import streamlit as st
import pandas as pd
import io
from sqlalchemy import text
from backend.db import engine, metadata

st.set_page_config(page_title="Auditoría del Sistema", layout="wide")
st.title("🧾 Auditoría del Sistema")

# ---------------------------
# Seguridad
# ---------------------------
if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()

# ---------------------------
# Cargar auditoría desde Neon
# ---------------------------
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT 
            id, 
            accion, 
            producto_id, 
            usuario, 
            fecha 
        FROM auditoria
        ORDER BY fecha DESC
    """)).mappings().all()

if not result:
    st.info("No hay registros de auditoría todavía.")
    st.stop()

df = pd.DataFrame(result)
df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
df["fecha_str"] = df["fecha"].dt.strftime("%Y-%m-%d %H:%M:%S")

# ---------------------------
# Sidebar de filtros
# ---------------------------
st.sidebar.header("Filtros de auditoría")

usuarios = sorted(df["usuario"].dropna().unique())
acciones = sorted(df["accion"].dropna().unique())

usuario_sel = st.sidebar.multiselect("Usuario", usuarios, default=usuarios)
accion_sel = st.sidebar.multiselect("Acción", acciones, default=acciones)

# Rango de fechas
fecha_min = df["fecha"].min().date() if not df.empty else None
fecha_max = df["fecha"].max().date() if not df.empty else None

rango_fechas = st.sidebar.date_input(
    "Rango de fechas",
    [fecha_min, fecha_max] if fecha_min and fecha_max else [None, None],
    format="YYYY-MM-DD"
)
if isinstance(rango_fechas, list) and len(rango_fechas) == 2:
    fecha_ini, fecha_fin = rango_fechas
else:
    fecha_ini = fecha_fin = None

# ---------------------------
# Aplicar filtros
# ---------------------------
filtro = df["usuario"].isin(usuario_sel) & df["accion"].isin(accion_sel)
if fecha_ini and fecha_fin:
    filtro &= df["fecha"].dt.date.between(fecha_ini, fecha_fin)

df_filtrado = df[filtro].sort_values("fecha", ascending=False)

# ---------------------------
# Buscador por producto o usuario
# ---------------------------
busqueda = st.text_input("🔍 Buscar por usuario, acción o ID de producto:")
if busqueda:
    mask = (
        df_filtrado["usuario"].str.contains(busqueda, case=False, na=False) |
        df_filtrado["accion"].str.contains(busqueda, case=False, na=False) |
        df_filtrado["producto_id"].astype(str).str.contains(busqueda, case=False, na=False)
    )
    df_filtrado = df_filtrado[mask]

# ---------------------------
# Mostrar auditoría
# ---------------------------
st.subheader(f"Resultados: {len(df_filtrado)} registros")

def color_por_accion(val):
    if val == "eliminar":
        return "background-color:#ffcccc;"
    elif val == "editar":
        return "background-color:#fff2cc;"
    elif val == "crear":
        return "background-color:#d9ead3;"
    return ""

if not df_filtrado.empty:
    df_display = df_filtrado[["fecha_str", "usuario", "accion", "producto_id"]].copy()
    df_display.rename(columns={
        "fecha_str": "Fecha",
        "usuario": "Usuario",
        "accion": "Acción",
        "producto_id": "Producto ID"
    }, inplace=True)

    st.dataframe(df_display.style.applymap(color_por_accion, subset=["Acción"]), use_container_width=True)

    # ---------------------------
    # Exportar a Excel
    # ---------------------------
    def exportar_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Auditoria")
        return output.getvalue()

    excel_data = exportar_excel(df_display)
    st.download_button(
        label="📥 Descargar auditoría en Excel",
        data=excel_data,
        file_name="auditoria_sistema.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("No hay registros que coincidan con los filtros.")

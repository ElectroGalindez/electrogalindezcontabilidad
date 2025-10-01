import streamlit as st
import pandas as pd
import json
import io
from backend.logs import listar_logs

st.set_page_config(page_title="Auditoría y Logs", layout="wide")
st.title("📝 Auditoría y Logs del Sistema")

# ---------------------------
# Seguridad
# ---------------------------
if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()

# ---------------------------
# Cargar logs
# ---------------------------
logs = listar_logs()
NIVELES_VALIDOS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Asegurar columna "nivel" consistente
for log in logs:
    nivel = log.get("nivel", "INFO").upper()
    log["nivel"] = nivel if nivel in NIVELES_VALIDOS else "INFO"

if not logs:
    st.info("No hay logs registrados aún.")
    st.stop()

df = pd.DataFrame(logs)
if "fecha" in df.columns:
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["fecha_str"] = df["fecha"].dt.strftime("%Y-%m-%d %H:%M:%S")

# ---------------------------
# Sidebar: filtros
# ---------------------------
st.sidebar.header("Filtros de logs")

niveles_sel = st.sidebar.multiselect("Nivel de log", NIVELES_VALIDOS, default=NIVELES_VALIDOS)
usuarios_sel = st.sidebar.multiselect("Usuario", sorted(df["usuario"].unique()), default=sorted(df["usuario"].unique()))
acciones_sel = st.sidebar.multiselect("Acción", sorted(df["accion"].unique()), default=sorted(df["accion"].unique()))

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
filtro = df["nivel"].isin(niveles_sel) & df["usuario"].isin(usuarios_sel) & df["accion"].isin(acciones_sel)
if fecha_ini and fecha_fin:
    filtro &= df["fecha"].dt.date.between(fecha_ini, fecha_fin)

logs_filtrados = df[filtro].sort_values("fecha", ascending=False)

# ---------------------------
# Colorear filas por nivel
# ---------------------------
def color_por_nivel(val):
    if val == "CRITICAL":
        return "background-color:#ff4d4d; color:white;"
    elif val == "ERROR":
        return "background-color:#ff9999;"
    elif val == "WARNING":
        return "background-color:#ffd699;"
    return ""

# ---------------------------
# Mostrar logs
# ---------------------------
st.subheader(f"Logs filtrados ({len(logs_filtrados)})")
if not logs_filtrados.empty:
    df_display = logs_filtrados.copy()
    df_display = df_display[["fecha_str", "usuario", "accion", "nivel", "detalles"]]
    df_display.rename(columns={"fecha_str": "Fecha", "usuario": "Usuario", "accion": "Acción", "nivel": "Nivel", "detalles": "Detalles"}, inplace=True)
    
    st.dataframe(df_display.style.applymap(color_por_nivel, subset=["Nivel"]), use_container_width=True)

    # Exportar a Excel
    df_export = df_display.copy()
    df_export["Detalles"] = df_export["Detalles"].apply(lambda x: json.dumps(x, ensure_ascii=False))
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_export.to_excel(writer, index=False, sheet_name="Logs")
    excel_data = output.getvalue()
    st.download_button(
        label="📥 Descargar logs en Excel",
        data=excel_data,
        file_name="logs_auditoria.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("No hay logs que cumplan los filtros seleccionados.")

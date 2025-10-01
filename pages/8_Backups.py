import streamlit as st
from pathlib import Path
from datetime import datetime
import io
import pandas as pd
from backend.backup import backup_data_folder, restore_backup
from protector import proteger_pagina

st.set_page_config(page_title="Backups automáticos", layout="wide")
st.title("🗄️ Backups automáticos de la base de datos")
st.info("Los backups automáticos se realizan cada vez que se inicia la aplicación o se accede a esta página. Puedes descargar el backup más reciente desde aquí.")

# ---------------------------
# Seguridad
# ---------------------------
if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()

def es_admin():
    return st.session_state.usuario.get("rol") == "admin"

# ---------------------------
# Carpeta de backups
# ---------------------------
backups_dir = Path(__file__).resolve().parents[2] / "backups"
backups_dir.mkdir(exist_ok=True)  # Crear si no existe

# ---------------------------
# Crear backup automático solo si no hay uno para hoy
# ---------------------------
today_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
backups = sorted([d for d in backups_dir.iterdir() if d.is_dir()], reverse=True)
backups_hoy = [b for b in backups if b.name.startswith(f"backup_{datetime.now().strftime('%Y%m%d')}")]

if not backups_hoy:
    try:
        _backup_path = backup_data_folder()
        st.success(f"Backup realizado correctamente en: {_backup_path}")
        backups = sorted([d for d in backups_dir.iterdir() if d.is_dir()], reverse=True)
    except Exception as e:
        st.error(f"No se pudo crear el backup: {e}")
else:
    st.info(f"Ya existe un backup para hoy: {backups_hoy[0].name}")

# ---------------------------
# Restaurar backup existente
# ---------------------------
st.subheader("🔄 Restaurar backup anterior")
if backups:
    backup_names = [b.name for b in backups]
    selected_backup = st.selectbox("Selecciona un backup para restaurar", backup_names, help="Esta acción sobrescribirá todos los datos actuales.")
    if st.button("Restaurar backup seleccionado"):
        if not es_admin():
            st.error("Solo los administradores pueden restaurar backups.")
        else:
            try:
                restore_backup(str(backups_dir / selected_backup))
                st.success(f"Backup '{selected_backup}' restaurado correctamente. Recarga la app para ver los datos actualizados.")
            except Exception as e:
                st.error(f"Error al restaurar backup: {e}")
else:
    st.info("No hay backups disponibles para restaurar.")

# ---------------------------
# Descargar backup de hoy
# ---------------------------
st.subheader("📥 Descargar backup de hoy")
backups_hoy = [b for b in backups if b.name.startswith(datetime.now().strftime('%Y%m%d'))]
if backups_hoy:
    b = backups_hoy[0]  # El más reciente del día
    files = list(b.glob("*.json"))
    if files:
        st.markdown(f"**{b.name}** ({len(files)} archivos)")
        for f in files:
            try:
                df = pd.read_json(f)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    df.to_excel(writer, index=False)
                excel_data = output.getvalue()
                st.download_button(
                    label=f"Descargar {f.stem}.xlsx",
                    data=excel_data,
                    file_name=f"{f.stem}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"dl_{b.name}_{f.stem}"
                )
            except Exception as e:
                st.caption(f"No se pudo convertir {f.name} a Excel: {e}")
    else:
        st.info("No hay archivos JSON en el backup de hoy.")
else:
    st.info("No hay backups generados hoy.")

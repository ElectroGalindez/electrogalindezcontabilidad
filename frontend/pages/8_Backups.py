import streamlit as st
from backend.backup import backup_data_folder
from protector import proteger_pagina

from pathlib import Path

st.set_page_config(page_title="Backups automáticos", layout="wide")
st.title("🗄️ Backups automáticos de la base de datos")
st.info("Los backups automáticos se realizan cada vez que se inicia la aplicación o se accede a esta página. Puedes descargar el backup más reciente desde aquí.")


if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()

def es_admin():
    return st.session_state.usuario.get("rol") == "admin"

# Solo crear backup si no existe uno para hoy
from datetime import datetime
today_str = datetime.now().strftime("%Y%m%d")
backups_dir = Path(__file__).resolve().parents[2] / "backups"
backups = sorted([d for d in backups_dir.iterdir() if d.is_dir()], reverse=True)
backups_hoy = [b for b in backups if b.name.startswith(f"backup_{today_str}")]
if not backups_hoy:
    _backup_path = backup_data_folder()
    if _backup_path:
        st.success(f"Backup realizado en: {_backup_path}")
    # Actualizar lista de backups para mostrar el nuevo
    backups = sorted([d for d in backups_dir.iterdir() if d.is_dir()], reverse=True)
    backups_hoy = [b for b in backups if b.name.startswith(f"backup_{today_str}")]
elif backups_hoy:
    st.info(f"Ya existe un backup para hoy: {backups_hoy[0].name}")


# Mostrar lista de backups disponibles
from pathlib import Path
backups_dir = Path(__file__).resolve().parents[2] / "backups"
backups = sorted([d for d in backups_dir.iterdir() if d.is_dir()], reverse=True)

st.subheader("Restaurar backup anterior")
if backups:
    backup_names = [b.name for b in backups]
    selected_backup = st.selectbox("Selecciona un backup para restaurar", backup_names, help="Esta acción sobrescribirá todos los datos actuales.")
    if st.button("Restaurar este backup", type="primary", help="Solo admin puede restaurar. Esta acción es irreversible."):
        if not es_admin():
            st.error("Solo los administradores pueden restaurar backups.")
        else:
            from backend.backup import restore_backup
            try:
                restore_backup(str(backups_dir / selected_backup))
                st.success(f"Backup '{selected_backup}' restaurado correctamente. Recarga la app para ver los datos actualizados.")
            except Exception as e:
                st.error(f"Error al restaurar backup: {e}")
else:
    st.info("No hay backups disponibles para restaurar.")

# Mostrar backup de hoy y descargas como antes
today_str = datetime.now().strftime("%Y%m%d")
backups_hoy = [b for b in backups if b.name.startswith(f"backup_{today_str}")]
if backups_hoy:
    b = backups_hoy[0]  # El más reciente del día
    st.subheader(f"Backup de hoy: {b.name}")
    files = list(b.glob("*.json"))
    if files:
        st.markdown(f"**{b.name}** ({len(files)} archivos)")
        for f in files:
            import pandas as pd
            import io
            try:
                df = pd.read_json(f)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    df.to_excel(writer, index=False)
                excel_data = output.getvalue()
                st.download_button(
                    label=f"Descargar {f.stem}.xlsx (Excel)",
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

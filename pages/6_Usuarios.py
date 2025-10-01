import streamlit as st
from backend.usuarios import listar_usuarios, crear_usuario, cambiar_password, cambiar_rol, desactivar_usuario, guardar_usuarios, cargar_usuarios
from backend.logs import obtener_logs_usuario
from protector import proteger_pagina

st.set_page_config(page_title="Gestión de Usuarios", layout="wide")

st.title("👤 Gestión de Usuarios")
st.caption("Administra los usuarios del sistema. Solo los administradores pueden acceder a esta página. Los campos obligatorios están marcados con *.")


if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()



usuarios = listar_usuarios()

# Filtros y búsqueda
st.subheader("🔎 Buscar y filtrar usuarios")
colf1, colf2 = st.columns(2)
with colf1:
    filtro_username = st.text_input("Buscar por usuario", "")
with colf2:
    filtro_rol = st.selectbox("Filtrar por rol", ["Todos"] + list(sorted(set(u["rol"] for u in usuarios))))

usuarios_filtrados = [
    u for u in usuarios
    if (filtro_username.lower() in u["username"].lower()) and (filtro_rol == "Todos" or u["rol"] == filtro_rol)
]

st.subheader("Usuarios registrados")
if usuarios_filtrados:
    for u in usuarios_filtrados:
        with st.expander(f"👤 {u['username']} ({'Activo' if u['activo'] else 'Inactivo'})", expanded=False):
            col1, col2, col3, col4 = st.columns([2,2,2,2])
            with col1:
                nuevo_nombre = st.text_input("Usuario", value=u["username"], key=f"edit_user_{u['username']}", disabled=True)
            with col2:
                nuevo_rol = st.selectbox("Rol", ["empleado", "admin"], index=["empleado", "admin"].index(u["rol"]), key=f"edit_rol_{u['username']}")
            with col3:
                nuevo_estado = st.selectbox("Estado", ["Activo", "Inactivo"], index=0 if u["activo"] else 1, key=f"edit_estado_{u['username']}")
            with col4:
                if st.button("💾 Guardar cambios", key=f"save_{u['username']}"):
                    usuarios_db = cargar_usuarios()
                    for user_db in usuarios_db:
                        if user_db["username"] == u["username"]:
                            user_db["rol"] = nuevo_rol
                            user_db["activo"] = (nuevo_estado == "Activo")
                    guardar_usuarios(usuarios_db)
                    st.success("Cambios guardados")
                    st.rerun()
            col5, col6 = st.columns([2,2])
            with col5:
                if st.button("🗑️ Eliminar usuario", key=f"delete_{u['username']}"):
                    if st.confirm(f"¿Seguro que deseas eliminar definitivamente el usuario '{u['username']}'? Esta acción no se puede deshacer.", key=f"conf_{u['username']}"):
                        usuarios_db = cargar_usuarios()
                        usuarios_db = [user_db for user_db in usuarios_db if user_db["username"] != u["username"]]
                        guardar_usuarios(usuarios_db)
                        st.warning(f"Usuario '{u['username']}' eliminado permanentemente.")
                        st.rerun()
            with col6:
                if st.button("📜 Ver historial de acciones", key=f"log_{u['username']}"):
                    logs = obtener_logs_usuario(u["username"])
                    if logs:
                        for log in logs:
                            st.write(f"{log['fecha']} - {log['accion']}: {log['detalles']}")
                    else:
                        st.info("Sin historial para este usuario.")
else:
    st.info("No hay usuarios que coincidan con los filtros.")

st.divider()


# Crear nuevo usuario
st.divider()
st.subheader("➕ Crear nuevo usuario")
with st.form("form_nuevo_usuario"):
    nuevo_user = st.text_input("Usuario *", help="Obligatorio. Mínimo 3 caracteres.")
    nuevo_pass = st.text_input("Contraseña *", type="password", help="Obligatorio. Mínimo 6 caracteres.")
    nuevo_rol = st.selectbox("Rol *", ["empleado", "admin"], help="Obligatorio.")
    submitted = st.form_submit_button("Crear usuario")
    if submitted:
        with st.spinner("Creando usuario..."):
            if len(nuevo_user) < 3:
                st.error("El usuario debe tener al menos 3 caracteres.")
            elif len(nuevo_pass) < 6:
                st.error("La contraseña debe tener al menos 6 caracteres.")
            else:
                try:
                    crear_usuario(nuevo_user, nuevo_pass, nuevo_rol, actor=st.session_state.usuario["username"])
                    st.success(f"Usuario '{nuevo_user}' creado ✅")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

st.divider()

# Cambiar contraseña y rol, desactivar usuario
st.subheader("🔧 Modificar usuario existente")
st.info("Selecciona un usuario activo para cambiar su contraseña, rol o desactivarlo. Solo los administradores pueden realizar estas acciones.")
usernames = [u["username"] for u in usuarios if u["activo"]]
if usernames:
    seleccionado = st.selectbox("Selecciona usuario *", usernames, help="Obligatorio. Solo usuarios activos.")
    col1, col2, col3 = st.columns(3)
    with col1:
        new_pass = st.text_input("Nueva contraseña *", key="newpass", help="Obligatorio. Mínimo 6 caracteres.")
        if st.button("Cambiar contraseña") and new_pass:
            with st.spinner("Actualizando contraseña..."):
                if len(new_pass) < 6:
                    st.error("La contraseña debe tener al menos 6 caracteres.")
                else:
                    cambiar_password(seleccionado, new_pass, actor=st.session_state.usuario["username"])
                    st.success("Contraseña actualizada ✅")
    with col2:
        nuevo_rol = st.selectbox("Nuevo rol *", ["empleado", "admin"], key="rol", help="Obligatorio.")
        if st.button("Cambiar rol"):
            with st.spinner("Actualizando rol..."):
                cambiar_rol(seleccionado, nuevo_rol, actor=st.session_state.usuario["username"])
                st.success("Rol actualizado ✅")
    with col3:
        if st.button("Desactivar usuario"):
            with st.spinner("Desactivando usuario..."):
                desactivar_usuario(seleccionado, actor=st.session_state.usuario["username"])
                st.warning("Usuario desactivado ❌")
                st.rerun()
else:
    st.info("No hay usuarios activos para modificar.")

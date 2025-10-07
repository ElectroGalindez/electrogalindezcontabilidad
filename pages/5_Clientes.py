import streamlit as st
from backend.clientes import list_clients, add_client, update_client, delete_client

st.set_page_config(page_title="Gestión de Clientes", layout="wide")
st.title("👥 Gestión de Clientes")
st.caption("Administra los clientes del sistema.")

# ---------------------------
# Verificar sesión
# ---------------------------
if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()

# ---------------------------
# Lista de clientes con filtros
# ---------------------------
clientes_data = list_clients()

st.subheader("🔎 Buscar y filtrar clientes")
col1, col2 = st.columns(2)
with col1:
    filtro_nombre = st.text_input("Buscar por nombre")
with col2:
    filtro_ci = st.text_input("Buscar por CI")

clientes_filtrados = [
    c for c in clientes_data
    if (filtro_nombre.lower() in c["nombre"].lower()) and (filtro_ci in c.get("ci", ""))
]

st.subheader("Clientes registrados")
if clientes_filtrados:
    for c in clientes_filtrados:
        with st.expander(f"{c['nombre']} ({c.get('ci', '')})", expanded=False):
            col1, col2, col3, col4, col5 = st.columns([2, 3, 2, 2, 2])
            with col1:
                nombre = st.text_input("Nombre", value=c["nombre"], key=f"nombre_{c['id']}")
            with col2:
                direccion = st.text_input("Dirección", value=c.get("direccion",""), key=f"direccion_{c['id']}")
            with col3:
                telefono = st.text_input("Teléfono", value=c.get("telefono",""), key=f"telefono_{c['id']}")
            with col4:
                ci = st.text_input("CI", value=c.get("ci",""), key=f"ci_{c['id']}")
            with col5:
                chapa = st.text_input("Chapa", value=c.get("chapa",""), key=f"chapa_{c['id']}")
            col6, col7 = st.columns(2)
            with col6:
                if st.button("💾 Guardar cambios", key=f"save_{c['id']}"):
                    update_client(
                        c["id"],
                        nombre=nombre,
                        direccion=direccion,
                        telefono=telefono,
                        ci=ci,
                        chapa=chapa
                    )
                    st.success("✅ Cliente actualizado")
                    st.status()
            with col7:
                if st.button("🗑 Eliminar cliente", key=f"del_{c['id']}"):
                    delete_client(c["id"])
                    st.success("❌ Cliente eliminado")
                    st.status()
else:
    st.info("No hay clientes que coincidan con los filtros.")

st.divider()

# ---------------------------
# Crear nuevo cliente
# ---------------------------
st.subheader("➕ Crear nuevo cliente")
with st.form("form_nuevo_cliente", clear_on_submit=True):
    nombre_nuevo = st.text_input("Nombre *")
    direccion_nueva = st.text_input("Dirección")
    telefono_nuevo = st.text_input("Teléfono")
    ci_nuevo = st.text_input("CI")
    chapa_nueva = st.text_input("Chapa")
    submitted = st.form_submit_button("Crear cliente")
    if submitted:
        if not nombre_nuevo.strip():
            st.error("❌ El nombre no puede estar vacío.")
        else:
            add_client(
                nombre=nombre_nuevo,
                direccion=direccion_nueva,
                telefono=telefono_nuevo,
                ci=ci_nuevo,
                chapa=chapa_nueva
            )
            st.success(f"✅ Cliente '{nombre_nuevo}' creado")
            st.status()

if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()
import streamlit as st
from backend import categorias

st.set_page_config(page_title="Categorías", layout="wide")
st.title("📂 Gestión de Categorías")

# =============================
# 1. Cargar categorías
# =============================
lista_categorias = categorias.cargar_categorias()

# =============================
# 2. Agregar nueva categoría
# =============================
st.subheader("➕ Agregar categoría")
with st.form("form_agregar"):
    nueva_categoria = st.text_input("Nombre de la categoría")
    submitted = st.form_submit_button("Agregar")
    if submitted:
        try:
            categorias.agregar_categoria(nueva_categoria)
            st.success(f"Categoría '{nueva_categoria}' agregada ✅")
            st.rerun()
        except ValueError as e:
            st.error(str(e))

st.divider()

# =============================
# 3. Editar o eliminar categorías existentes
# =============================
st.subheader("✏️ Editar / 🗑️ Eliminar Categorías")

# Cargar categorías
lista_categorias = categorias.cargar_categorias()

if not lista_categorias:
    st.info("No hay categorías registradas. Agrega nuevas categorías arriba.")
else:
    # Selector de categoría
    seleccionada = st.selectbox("Selecciona una categoría para editar:", [""] + lista_categorias)

    if seleccionada:
        st.markdown("---")
        st.write(f"**Editar categoría:** {seleccionada}")

        # Formulario para editar/eliminar
        with st.form(key=f"form_{seleccionada}"):
            nuevo_nombre = st.text_input("Nuevo nombre:", value=seleccionada)
            col1, col2 = st.columns(2)
            
            with col1:
                guardar = st.form_submit_button("💾 Guardar")
            with col2:
                eliminar = st.form_submit_button("🗑️ Eliminar")

            if guardar:
                if nuevo_nombre.strip() == "":
                    st.error("El nombre no puede estar vacío.")
                elif nuevo_nombre in lista_categorias and nuevo_nombre != seleccionada:
                    st.error(f"Ya existe la categoría '{nuevo_nombre}'.")
                else:
                    categorias.editar_categoria(seleccionada, nuevo_nombre)
                    st.success(f"Categoría '{seleccionada}' renombrada a '{nuevo_nombre}' ✅")
                    st.rerun()

            if eliminar:
                categorias.eliminar_categoria(seleccionada)
                st.warning(f"Categoría '{seleccionada}' eliminada ❌")
                st.rerun()

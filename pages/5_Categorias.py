# pages/5_Categorias.py
import streamlit as st
import pandas as pd
from backend import categorias, productos

st.set_page_config(page_title="Categorías", layout="wide")
st.title("📂 Gestión de Categorías")

# ---------------------------
# Verificar sesión
# ---------------------------
if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()
# ---------------------------
# Cargar categorías
# ---------------------------
lista_categorias = categorias.list_categories()
df = pd.DataFrame(lista_categorias)

# ---------------------------
# Buscador
# ---------------------------
busqueda = st.text_input("🔍 Buscar por nombre o ID:")
df_filtrado = df.copy()
if busqueda:
    mask = (
        df_filtrado["nombre"].str.contains(busqueda, case=False, na=False) |
        df_filtrado["id"].astype(str).str.contains(busqueda)
    )
    df_filtrado = df_filtrado[mask]

st.dataframe(df_filtrado, width='stretch')

# ---------------------------
# Formulario Crear / Editar
# ---------------------------

import streamlit as st
from backend import categorias

st.title("📦 Gestión de Categorías")

# === Mostrar todas las categorías ===
todas = categorias.list_categories()
nombres = [c["nombre"] for c in todas]

categoria_actual = None
if nombres:
    nombre_sel = st.selectbox("Selecciona una categoría", nombres)
    categoria_actual = next((c for c in todas if c["nombre"] == nombre_sel), None)
else:
    st.info("No hay categorías creadas todavía.")

# === Crear nueva categoría ===
st.subheader("➕ Crear nueva categoría")
with st.form("crear_categoria"):
    nuevo_nombre = st.text_input("Nombre de la categoría")
    if st.form_submit_button("Guardar"):
        if nuevo_nombre.strip():
            categorias.agregar_categoria(nuevo_nombre.strip(), usuario="admin")
            st.success(f"Categoría '{nuevo_nombre}' creada correctamente ✅")
            st.rerun()
        else:
            st.warning("El nombre no puede estar vacío.")

# === Editar categoría existente ===
if categoria_actual:
    st.subheader("✏️ Editar categoría seleccionada")
    with st.form("editar_categoria"):
        nuevo_nombre = st.text_input("Nuevo nombre", categoria_actual["nombre"])
        if st.form_submit_button("Actualizar"):
            if nuevo_nombre.strip():
                categorias.editar_categoria(categoria_actual["id"], nuevo_nombre.strip(), usuario="admin")
                st.success(f"Categoría actualizada a '{nuevo_nombre}' ✅")
                st.rerun()
            else:
                st.warning("El nombre no puede estar vacío.")

# === Eliminar categoría ===
st.subheader("🗑️ Eliminar categoría")

if categoria_actual:
    asociados = categorias.list_products_by_category(categoria_actual["id"])

    if asociados:
        st.warning(
            f"No puedes eliminar la categoría '{categoria_actual['nombre']}' "
            f"porque tiene {len(asociados)} productos asociados."
        )

        # Mostrar lista breve de productos (opcional)
        with st.expander("Ver productos asociados"):
            for p in asociados:
                st.text(f"- {p['nombre']} (ID: {p['id']})")
    else:
        confirmar = st.checkbox(
            f"Sí, quiero eliminar la categoría '{categoria_actual['nombre']}'"
        )

        if confirmar and st.button("Eliminar definitivamente"):
            try:
                categorias.eliminar_categoria(
                    categoria_actual["id"],
                    usuario=st.session_state.usuario["username"]
                )
                st.success(f"Categoría '{categoria_actual['nombre']}' eliminada correctamente ✅")
                st.rerun()
            except Exception as e:
                st.error(f"Error al eliminar: {str(e)}")
else:
    st.info("Selecciona una categoría para eliminar.")

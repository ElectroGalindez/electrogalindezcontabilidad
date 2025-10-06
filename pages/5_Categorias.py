import streamlit as st
import pandas as pd
from backend import categorias

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
st.markdown("### ✏️ Crear / Editar Categoría")

# Seleccionar categoría existente para editar
opciones = [""] + [f"{c['nombre']} | ID:{c['id']}" for c in lista_categorias]
seleccionado = st.selectbox("Selecciona una categoría para editar (opcional):", opciones, key="cat_select")

categoria_actual = None
if seleccionado and seleccionado != "":
    cat_id = int(seleccionado.split("ID:")[-1])
    categoria_actual = categorias.get_category(cat_id)

# Input para nombre
nombre = st.text_input(
    "Nombre de la categoría",
    value=categoria_actual["nombre"] if categoria_actual else "",
    key="cat_nombre"
)

# Botones
col1, col2 = st.columns([1,1])

# Guardar
with col1:
    if st.button("💾 Guardar Categoría"):
        if categoria_actual:
            categorias.editar_categoria(categoria_actual["id"], nombre)
            st.success(f"Categoría '{nombre}' actualizada ✅")
        else:
            categorias.agregar_categoria(nombre)
            st.success(f"Categoría '{nombre}' creada ✅")
        st.experimental_rerun()

# Eliminar
with col2:
    if categoria_actual and st.button("🗑️ Eliminar Categoría"):
        categorias.eliminar_categoria(categoria_actual["id"])
        st.warning(f"Categoría '{categoria_actual['nombre']}' eliminada ❌")
        st.experimental_rerun()

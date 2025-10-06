# pages/1_Inventario.py
import streamlit as st
import pandas as pd
import io
from backend import productos, categorias

st.set_page_config(page_title="Inventario", layout="wide")
st.title("📦 Gestión de Inventario")

# ---------------------------
# Verificar sesión
# ---------------------------
if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()

# ---------------------------
# Variables de sesión
# ---------------------------
if 'reload' not in st.session_state:
    st.session_state.reload = False

# ---------------------------
# Cargar productos y categorías
# ---------------------------
productos_lista = productos.list_products()
categorias_lista = categorias.list_categories()

# Mapear categorías id <-> nombre
cat_id_to_name = {c["id"]: c["nombre"] for c in categorias_lista}
cat_name_to_id = {c["nombre"]: c["id"] for c in categorias_lista}

# ---------------------------
# Preparar DataFrame para mostrar inventario
# ---------------------------
df_display = pd.DataFrame([{
    "ID": p.get("id", ""),
    "Nombre": p.get("nombre", ""),
    "Categoría": cat_id_to_name.get(p.get("categoria_id", ""), ""),
    "Cantidad": int(p.get("cantidad", 0)),
    "Precio": float(p.get("precio", 0.0))
} for p in productos_lista])

# Formatear precios
df_display["Precio"] = df_display["Precio"].apply(lambda x: f"${x:,.2f}")

# Resaltar stock bajo
def color_stock(val):
    return 'background-color: #ffcccc' if val <= 5 else ''

# ---------------------------
# Buscador avanzado con filtrado dinámico
# ---------------------------
busqueda = st.text_input("🔍 Buscar por nombre, categoría o ID:", key="busqueda_inventario")
if busqueda:
    mask = (
        df_display["Nombre"].str.contains(busqueda, case=False, na=False) |
        df_display["Categoría"].str.contains(busqueda, case=False, na=False) |
        df_display["ID"].astype(str).str.contains(busqueda)
    )
    df_filtrado = df_display[mask]
else:
    df_filtrado = df_display

# Mostrar DataFrame filtrado
st.dataframe(df_filtrado.style.applymap(color_stock, subset=["Cantidad"]), use_container_width=True)

# ---------------------------
# Formulario Crear / Editar
# ---------------------------
st.markdown('<div class="subtitulo">✏️ Crear / Editar Producto</div>', unsafe_allow_html=True)

seleccionado = st.selectbox(
    "Selecciona un producto para editar (opcional):",
    options=[("", "")] + [(f"{p['nombre']} | {cat_id_to_name.get(p['categoria_id'], '')} | {p['id']}", p["id"]) for p in productos_lista],
    format_func=lambda x: x[0],
    key="select_producto"
)

# Desempaquetar
seleccionado_nombre, seleccionado_id = seleccionado


# Obtener producto actual
producto_actual = productos.get_product(seleccionado_id) if seleccionado_id else None

# Columnas del formulario
colA, colB = st.columns([2,1])
with colA:
    nombre = st.text_input("Nombre del producto", value=producto_actual["nombre"] if producto_actual else "")
    categoria_nombre = st.selectbox(
        "Categoría",
        options=[c["nombre"] for c in categorias_lista],
        index=[c["id"] for c in categorias_lista].index(producto_actual["categoria_id"]) if producto_actual else 0
    )
with colB:
    precio = st.number_input(
        "Precio",
        value=float(producto_actual["precio"]) if producto_actual else 0.0,
        step=0.01,
        format="%.2f"
    )
    cantidad = st.number_input(
        "Cantidad",
        value=int(producto_actual["cantidad"]) if producto_actual else 0,
        min_value=0,
        step=1
    )

# ---------------------------
# Botones de acción
# ---------------------------
col1, col2, col3 = st.columns([1,1,1])
cat_id = cat_name_to_id[categoria_nombre]

# Guardar
with col1:
    if st.button("💾 Guardar"):
        if producto_actual:
            productos.editar_producto(producto_actual["id"], {
                "nombre": nombre,
                "precio": precio,
                "cantidad": cantidad,
                "categoria_id": cat_id
            }, usuario=st.session_state.usuario["username"])
            st.success(f"Producto '{nombre}' actualizado ✅")
        else:
            productos.agregar_producto(nombre, precio, cantidad, cat_id, usuario=st.session_state.usuario["username"])
            st.success(f"Producto '{nombre}' creado ✅")
        st.experimental_rerun()

# Eliminar
with col2:
    if producto_actual and st.button("🗑️ Eliminar"):
        productos.eliminar_producto(producto_actual["id"], usuario=st.session_state.usuario["username"])
        st.warning(f"Producto '{producto_actual['nombre']}' eliminado ❌")
        st.experimental_rerun()

# Descargar Excel
with col3:
    def descargar_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Inventario")
        return output.getvalue()

    excel_data = descargar_excel(pd.DataFrame(productos.list_products()))
    st.download_button(
        label="📥 Descargar Inventario",
        data=excel_data,
        file_name="inventario.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

import streamlit as st
import pandas as pd
from backend import productos, categorias
import io

st.set_page_config(page_title="Inventario", layout="wide")
st.title("📦 Inventario de Productos")

# =============================
# Variables de sesión
# =============================
if 'reload' not in st.session_state:
    st.session_state.reload = False

# =============================
# Cargar productos y categorías
# =============================
productos_lista = productos.list_products()
categorias_lista = categorias.cargar_categorias()

# =============================
# Buscador avanzado
# =============================
df = pd.DataFrame(productos_lista)
busqueda = st.text_input("🔍 Buscar por nombre, categoría o ID:")
if busqueda:
    df = df[
        df["nombre"].str.contains(busqueda, case=False, na=False) |
        df["categoria"].str.contains(busqueda, case=False, na=False) |
        df["id"].str.contains(busqueda, case=False, na=False)
    ]

# Resaltar stock bajo
def color_stock(val):
    if val <= 5:
        return 'background-color: #ffcccc'  # rojo suave
    return ''

df_display = df.copy()
df_display["precio"] = df_display["precio"].apply(lambda x: f"${x:,.2f}")
st.dataframe(df_display.style.applymap(color_stock, subset=["cantidad"]), use_container_width=True)

st.divider()

# =============================
# Formulario de Crear / Editar
# =============================
st.subheader("✏️ Crear / Editar Producto")

# Selector de producto a editar
opciones_productos = [""] + [f"{p['nombre']} | {p['categoria']} | {p['id']}" for p in productos_lista]
seleccionado = st.selectbox("Selecciona un producto para editar:", opciones_productos)

producto_actual = None
if seleccionado:
    producto_id = seleccionado.split(" | ")[-1]
    producto_actual = productos.get_product(producto_id)

# Campos del formulario
nombre = st.text_input("Nombre del producto", value=producto_actual["nombre"] if producto_actual else "")
precio = st.number_input(
    "Precio",
    value=float(producto_actual["precio"]) if producto_actual else 0.0,
    step=0.01,
    format="%.2f"
)
cantidad = st.number_input(
    "Cantidad",
    value=int(producto_actual["cantidad"]) if producto_actual else 0,
    step=1
)

# =============================
# Categoría segura para selectbox
# =============================
if producto_actual:
    if producto_actual["categoria"] not in categorias_lista:
        categorias_lista.append(producto_actual["categoria"])
    selected_index = categorias_lista.index(producto_actual["categoria"])
else:
    selected_index = 0

categoria = st.selectbox(
    "Categoría",
    options=categorias_lista,  # ✅ correcto
    index=selected_index
)

# =============================
# Botones de acción
# =============================
col1, col2, col3 = st.columns([1,1,1])

with col1:
    if st.button("💾 Guardar"):
        try:
            if producto_actual:
                # Editar producto existente
                productos.editar_producto(producto_actual["id"], {
                    "nombre": nombre,
                    "precio": precio,
                    "cantidad": cantidad,
                    "categoria": categoria
                })
                st.success(f"Producto '{nombre}' actualizado ✅")
            else:
                # Validar si ya existe el nombre
                existentes = [p for p in productos.list_products() if p["nombre"].lower() == nombre.lower()]
                if existentes:
                    st.error(f"Ya existe un producto con el nombre '{nombre}'.")
                else:
                    productos.agregar_producto(nombre, precio, cantidad, categoria)
                    st.success(f"Producto '{nombre}' creado ✅")
            st.session_state.reload = not st.session_state.reload
        except ValueError as e:
            st.error(str(e))


with col2:
    if producto_actual and st.button("🗑️ Eliminar"):
        productos.eliminar_producto(producto_actual["id"])
        st.warning(f"Producto '{producto_actual['nombre']}' eliminado ❌")
        st.session_state.reload = not st.session_state.reload

with col3:
    # =============================
    # Descargar Excel
    # =============================
    def descargar_excel(df):
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine="xlsxwriter")
        df.to_excel(writer, index=False, sheet_name="Inventario")
        writer.close()
        processed_data = output.getvalue()
        return processed_data

    excel_data = descargar_excel(pd.DataFrame(productos.list_products()))
    st.download_button(
        label="📥 Descargar Inventario",
        data=excel_data,
        file_name="inventario.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# =============================
# Recarga controlada
# =============================
if st.session_state.reload:
    st.session_state.reload = False
    

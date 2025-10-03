import streamlit as st
import pandas as pd
from backend import productos, categorias
import io

st.set_page_config(page_title="Inventario", layout="wide")
st.title("📦 Gestión de Inventario")

if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()

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
# Preparar DataFrame seguro para mostrar inventario
# =============================
productos_lista = productos.list_products()
categorias_lista = categorias.cargar_categorias()

# Convertimos productos en DataFrame asegurando todas las claves
df_display = pd.DataFrame([{
    "id": p.get("id", ""),
    "nombre": p.get("nombre", ""),
    "categoria": p.get("categoria", ""),
    "cantidad": int(p.get("cantidad", 0)),
    "precio": float(p.get("precio", 0.0))
} for p in productos_lista])

# Asegurar columnas por si vienen vacías
for col in ["id", "nombre", "categoria", "cantidad", "precio"]:
    if col not in df_display.columns:
        df_display[col] = 0 if col in ["cantidad", "precio"] else ""

# Formatear precios
df_display["precio"] = df_display["precio"].apply(lambda x: f"${x:,.2f}")

# Función para resaltar stock bajo
def color_stock(val):
    return 'background-color: #ffcccc' if val <= 5 else ''

# Mostrar DataFrame
st.dataframe(df_display.style.applymap(color_stock, subset=["cantidad"]), use_container_width=True)

# =============================
# Buscador avanzado
# =============================
busqueda = st.text_input("🔍 Buscar por nombre, categoría o ID:")
df_filtrado = df_display.copy()
if busqueda:
    mask = (
        df_filtrado["nombre"].str.contains(busqueda, case=False, na=False) |
        df_filtrado["categoria"].str.contains(busqueda, case=False, na=False) |
        df_filtrado["id"].str.contains(busqueda, case=False, na=False)
    )
    df_filtrado = df_filtrado[mask]

# =============================
# Formulario Crear / Editar
# =============================
st.markdown('<div class="subtitulo">✏️ Crear / Editar Producto</div>', unsafe_allow_html=True)

# Selector opcional de producto
opciones_productos = [""] + [f"{p['nombre']} | {p['categoria']} | ID:{p['id']}" for p in productos_lista]
seleccionado = st.selectbox("Selecciona un producto para editar (opcional):", opciones_productos)

producto_actual = None
selected_index = 0
if seleccionado:
    producto_id = seleccionado.split("ID:")[-1]
    producto_actual = productos.get_product(producto_id)
    if producto_actual and producto_actual.get("categoria") not in categorias_lista:
        categorias_lista.append(producto_actual["categoria"])
        selected_index = categorias_lista.index(producto_actual["categoria"])

# Formulario
colA, colB = st.columns([2,1])
with colA:
    nombre = st.text_input("Nombre del producto", value=producto_actual.get("nombre", "") if producto_actual else "")
    categoria = st.selectbox("Categoría", options=categorias_lista, index=selected_index if producto_actual else 0)
with colB:
    precio = st.number_input("Precio", value=float(producto_actual.get("precio", 0.0)) if producto_actual else 0.0, step=0.01, format="%.2f")
    cantidad = st.number_input(
        "Cantidad (stock actual: {})".format(producto_actual.get("cantidad", 0)) if producto_actual else "Cantidad",
        value=int(producto_actual.get("cantidad", 0)) if producto_actual else 0,
        min_value=0,
        step=1
    )

# =============================
# Botones de acción
# =============================
col1, col2, col3 = st.columns([1,1,1])

# Guardar
with col1:
    if st.button("💾 Guardar"):
        try:
            if producto_actual:
                productos.editar_producto(producto_actual["id"], {
                    "nombre": nombre,
                    "precio": precio,
                    "cantidad": cantidad,
                    "categoria": categoria
                })
                st.success(f"Producto '{nombre}' actualizado ✅")
            else:
                existentes = [p for p in productos.list_products() if p["nombre"].lower() == nombre.lower()]
                if existentes:
                    st.error(f"Ya existe un producto con el nombre '{nombre}'.")
                else:
                    productos.agregar_producto(nombre, precio, cantidad, categoria)
                    st.success(f"Producto '{nombre}' creado ✅")
            st.session_state.reload = True
        except ValueError as e:
            st.error(str(e))

# Eliminar
with col2:
    if producto_actual and st.button("🗑️ Eliminar"):
        productos.eliminar_producto(producto_actual["id"])
        st.warning(f"Producto '{producto_actual['nombre']}' eliminado ❌")
        st.session_state.reload = True

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

# =============================
# Recarga controlada
# =============================
if st.session_state.reload:
    st.session_state.reload = False

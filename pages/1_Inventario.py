# pages/1_Inventario.py
import streamlit as st
import pandas as pd
import io
from backend import productos, categorias

st.set_page_config(page_title="Inventario", layout="wide")
st.title("📦 Gestión de Inventario")

# ---------------------------
# VALIDAR SESIÓN
# ---------------------------
if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()

# ---------------------------
# CARGA OPTIMIZADA DE DATOS
# ---------------------------
@st.cache_data(ttl=60)
def load_data():
    return {
        "productos": productos.list_products() or [],
        "categorias": categorias.list_categories() or []
    }

data = load_data()
productos_lista = data["productos"]
categorias_lista = data["categorias"]

# Mapa categoría
cat_id_to_name = {c["id"]: c["nombre"] for c in categorias_lista}

# ---------------------------
# DATAFRAME PARA MOSTRAR INVENTARIO
# ---------------------------
df_display = pd.DataFrame([
    {
        "ID": p["id"],
        "Nombre": p["nombre"],
        "Categoría": cat_id_to_name.get(p.get("categoria_id")),
        "Cantidad": p.get("cantidad", 0),
        "Precio": p.get("precio", 0.0),
    } for p in productos_lista
])

# Formato precio
df_display["Precio"] = df_display["Precio"].apply(lambda x: f"${x:,.2f}")


# Color stock
def color_stock(val):
    return "background-color: #ffcccc" if val <= 5 else ""

# ---------------------------
# BUSCADOR AVANZADO
# ---------------------------
busqueda = st.text_input("🔍 Buscar por nombre, categoría o ID:")

if busqueda:
    b = busqueda.lower()
    mask = (
        df_display["Nombre"].str.lower().str.contains(b) |
        df_display["Categoría"].str.lower().str.contains(b, na=False) |
        df_display["ID"].astype(str).str.contains(b)
    )
    df_filtrado = df_display[mask]
else:
    df_filtrado = df_display

st.dataframe(
    df_filtrado.style.applymap(color_stock, subset=["Cantidad"]),
    use_container_width=True
)

# ---------------------------
# FORMULARIO CREAR / EDITAR
# ---------------------------
st.markdown("### ✏️ Crear / Editar Producto")

# Selector de producto
opciones = [("", None)] + [
    (f"{p['nombre']} | {cat_id_to_name.get(p['categoria_id'])} | {p['id']}", p["id"])
    for p in productos_lista
]

seleccion = st.selectbox(
    "Selecciona un producto para editar (opcional):",
    options=opciones,
    format_func=lambda x: x[0] if isinstance(x, tuple) else "",
)

producto_id = seleccion[1] if isinstance(seleccion, tuple) else None
producto_actual = productos.get_product(producto_id) if producto_id else None

# Formulario
colA, colB = st.columns([2, 1])

with colA:
    nombre = st.text_input(
        "Nombre",
        value=producto_actual["nombre"] if producto_actual else ""
    )

    categoria_nombre = st.selectbox(
        "Categoría",
        options=[c["nombre"] for c in categorias_lista],
        index=(
            [c["id"] for c in categorias_lista].index(producto_actual["categoria_id"])
            if producto_actual else 0
        )
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

# Obtener ID de categoría
categoria_id = next((c["id"] for c in categorias_lista if c["nombre"] == categoria_nombre), None)

# ---------------------------
# BOTONES
# ---------------------------
col1, col2, col3 = st.columns([1, 1, 1])

# Guardar / Crear
with col1:
    if st.button("💾 Guardar"):
        productos.guardar_producto(
            nombre=nombre,
            precio=precio,
            cantidad=cantidad,
            categoria_id=categoria_id,
            usuario=st.session_state.usuario["username"]
        )
        st.success("Producto guardado correctamente")
        st.rerun()

# Eliminar
with col2:
    if producto_actual and st.button("🗑️ Eliminar"):
        productos.eliminar_producto(
            producto_actual["id"],
            usuario=st.session_state.usuario["username"]
        )
        st.warning("Producto eliminado")
        st.rerun()

# Exportar Excel
with col3:

    @st.cache_data
    def generar_excel(productos):
        df = pd.DataFrame(productos)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Inventario")
        return output.getvalue()

    excel = generar_excel(productos_lista)

    st.download_button(
        label="📥 Descargar Inventario",
        data=excel,
        file_name="inventario.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

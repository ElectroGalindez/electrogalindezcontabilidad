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

usuario_actual = st.session_state.usuario["username"]

# ---------------------------
# CATEGORÍAS (cache)
# ---------------------------
@st.cache_data(ttl=60)
def load_categories():
    cats = categorias.list_categories() or []
    return cats, {c["id"]: c["nombre"] for c in cats}

categorias_lista, cat_id_to_name = load_categories()

# ---------------------------
# PRODUCTOS (sin cache para reflejar cambios inmediatos)
# ---------------------------
def load_products():
    prods = productos.list_products() or []
    return prods

productos_lista = load_products()

# ---------------------------
# DATAFRAME PARA MOSTRAR INVENTARIO
# ---------------------------
def build_df(prods):
    df = pd.DataFrame([
        {
            "ID": p["id"],
            "Nombre": p["nombre"],
            "Categoría": cat_id_to_name.get(p.get("categoria_id"), ""),
            "Cantidad": p.get("cantidad", 0),
            "Precio": p.get("precio", 0.0),
        } for p in prods
    ])
    df["Precio"] = df["Precio"].apply(lambda x: f"${x:,.2f}")
    df["Cantidad"] = df["Cantidad"].astype(int)
    return df

def style_df(df):
    return df.style.applymap(lambda x: "background-color:#ffcccc" if isinstance(x,int) and x <=5 else "", subset=["Cantidad"]) \
                   .set_properties(**{"text-align": "right"})

# ---------------------------
# BUSCADOR
# ---------------------------
busqueda = st.text_input("🔍 Buscar por nombre, categoría o ID:")
df_display = build_df(productos_lista)
if busqueda:
    b = busqueda.lower()
    mask = (
        df_display["Nombre"].str.lower().str.contains(b) |
        df_display["Categoría"].str.lower().str.contains(b, na=False) |
        df_display["ID"].astype(str).str.contains(b)
    )
    df_display = df_display[mask]

st.dataframe(style_df(df_display), use_container_width=True)

# ---------------------------
# FORMULARIO CREAR / EDITAR
# ---------------------------
st.markdown("### ✏️ Crear / Editar Producto")

opciones = [("", None)] + [
    (f"{p['nombre']} | {cat_id_to_name.get(p['categoria_id'],'')} | {p['id']}", p["id"])
    for p in productos_lista
]

seleccion = st.selectbox(
    "Selecciona un producto para editar (opcional):",
    options=opciones,
    format_func=lambda x: x[0] if isinstance(x, tuple) else "",
)

producto_id = seleccion[1] if isinstance(seleccion, tuple) else None
producto_actual = productos.get_product(producto_id) if producto_id else None

colA, colB = st.columns([2,1])
with colA:
    nombre = st.text_input("Nombre", value=producto_actual["nombre"] if producto_actual else "")
    categoria_nombre = st.selectbox(
        "Categoría",
        options=[c["nombre"] for c in categorias_lista],
        index=[c["id"] for c in categorias_lista].index(producto_actual["categoria_id"]) if producto_actual else 0
    )
with colB:
    precio = st.number_input("Precio", value=float(producto_actual["precio"]) if producto_actual else 0.0, step=0.01, format="%.2f")
    cantidad = st.number_input("Cantidad", value=int(producto_actual["cantidad"]) if producto_actual else 0, min_value=0, step=1)

categoria_id = next((c["id"] for c in categorias_lista if c["nombre"] == categoria_nombre), None)

# ---------------------------
# BOTONES DE ACCIÓN
# ---------------------------
col1, col2, col3 = st.columns([1,1,1])

# Guardar / Crear producto
with col1:
    if st.button("💾 Guardar"):
        try:
            if producto_actual:
                productos.editar_producto(
                    producto_id=producto_actual["id"],
                    nombre=nombre,
                    precio=precio,
                    cantidad=cantidad,
                    categoria_id=categoria_id,
                    usuario=usuario_actual
                )
                st.success(f"Producto '{nombre}' actualizado ✅")
            else:
                productos.guardar_producto(
                    nombre=nombre,
                    precio=precio,
                    cantidad=cantidad,
                    categoria_id=categoria_id,
                    usuario=usuario_actual
                )
                st.success(f"Producto '{nombre}' creado ✅")
            # Recargar lista de productos inmediatamente
            productos_lista = load_products()
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Eliminar producto
with col2:
    if producto_actual:
        confirm = st.checkbox(f"Confirmar eliminación de '{producto_actual['nombre']}'")
        if confirm and st.button("🗑️ Eliminar"):
            try:
                productos.eliminar_producto(producto_actual["id"], usuario=usuario_actual)
                st.success(f"Producto '{producto_actual['nombre']}' eliminado ✅")
                productos_lista = load_products()
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Exportar Excel
with col3:
    def generar_excel(data):
        df = pd.DataFrame(data)
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

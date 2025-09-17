import streamlit as st
from backend.productos import list_products, add_product, edit_product, delete_product
from backend.exceptions import ValidationError, NotFoundError

st.title("📦 Inventario de Productos")

# Mostrar tabla de productos
productos = list_products()
st.subheader("Lista de Productos")
st.table(productos)

# Formulario agregar producto
st.subheader("Agregar Producto")
with st.form("add_product"):
    id = st.text_input("ID")
    nombre = st.text_input("Nombre")
    precio = st.number_input("Precio", min_value=0.0)
    cantidad = st.number_input("Cantidad", min_value=0)
    categoria = st.text_input("Categoría")
    submitted = st.form_submit_button("Agregar")
    if submitted:
        try:
            add_product({"id": id, "nombre": nombre, "precio": precio, "cantidad": cantidad, "categoria": categoria})
            st.success("Producto agregado")
        except ValidationError as e:
            st.error(str(e))

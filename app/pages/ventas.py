import streamlit as st
from backend.clientes import list_clients
from backend.productos import list_products
from backend.ventas import register_sale
from backend.exceptions import NotFoundError, InsufficientStockError

st.title("🛒 Registrar Venta")

clientes = list_clients()
productos = list_products()

cliente = st.selectbox("Seleccionar Cliente", [f"{c['id']} - {c['nombre']}" for c in clientes])
cliente_id = cliente.split(" - ")[0]

productos_seleccionados = st.multiselect(
    "Seleccionar Productos",
    [f"{p['id']} - {p['nombre']} (${p['precio']}) - Stock: {p['cantidad']}" for p in productos]
)

cantidades = {}
for prod in productos_seleccionados:
    prod_id = prod.split(" - ")[0]
    max_stock = next(p['cantidad'] for p in productos if p['id'] == prod_id)
    cantidades[prod_id] = st.number_input(f"Cantidad de {prod}", min_value=1, max_value=max_stock, value=1)

pagado = st.number_input("Monto pagado", min_value=0.0)

if st.button("Registrar Venta"):
    items = [{"id": pid, "cantidad": qty} for pid, qty in cantidades.items()]
    try:
        sale = register_sale(cliente_id, items, pagado)
        st.success(f"Venta registrada. Total: {sale['total']}, Pagado: {sale['pagado']}")
    except (NotFoundError, InsufficientStockError) as e:
        st.error(str(e))

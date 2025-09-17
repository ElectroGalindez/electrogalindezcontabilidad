import streamlit as st
from backend.clientes import list_clients, update_client_debt

st.title("💳 Deudas de Clientes")

clientes = [c for c in list_clients() if c["deuda_total"] > 0]
cliente = st.selectbox("Seleccionar Cliente", [f"{c['id']} - {c['nombre']} - Deuda: {c['deuda_total']}" for c in clientes])

monto = st.number_input("Monto a pagar", min_value=0.0)

if st.button("Registrar Pago"):
    cliente_id = cliente.split(" - ")[0]
    update_client_debt(cliente_id, -monto)
    st.success("Pago registrado correctamente")

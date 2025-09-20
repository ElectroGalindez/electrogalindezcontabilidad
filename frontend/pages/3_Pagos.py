# frontend/pages/3_Pagos.py
import streamlit as st
import pandas as pd
from backend import clientes, deudas

st.title("💳 Pagos de Clientes")

# ---------------------------
# CLIENTE INDIVIDUAL
# ---------------------------
clientes_data = clientes.list_clients()
clientes_dict = {c["nombre"]: c["id"] for c in clientes_data}

if not clientes_dict:
    st.warning("⚠️ No hay clientes registrados.")
else:
    cliente_nombre = st.selectbox("Seleccionar cliente", list(clientes_dict.keys()))
    cliente_id = clientes_dict[cliente_nombre]

    # Mostrar solo deudas pendientes
    deudas_cliente = deudas.debts_by_client(cliente_id)
    deudas_pendientes = [d for d in deudas_cliente if d["estado"] == "pendiente" and d["monto"] > 0]

    if not deudas_pendientes:
        st.info("✅ Este cliente no tiene deudas pendientes.")
    else:
        df = pd.DataFrame(deudas_pendientes)
        st.dataframe(df, use_container_width=True)

        deuda_ids = [d["id"] for d in deudas_pendientes]
        deuda_id = st.selectbox("Selecciona deuda a pagar", deuda_ids)

        monto_pago = st.number_input("Monto a pagar", min_value=0.0, step=0.01)
        if st.button("💾 Registrar Pago"):
            updated = deudas.pay_debt(deuda_id, monto_pago)
            st.success(
                f"✅ Pago registrado. Estado deuda: **{updated['estado']}**, "
                f"Monto restante: ${updated['monto']:,.2f}"
            )
            st.rerun()

# ---------------------------
# TABLA DE CLIENTES CON DEUDA
# ---------------------------
st.subheader("📊 Clientes con deuda pendiente")

clientes_con_deuda = []
for c in clientes_data:
    deudas_c = deudas.debts_by_client(c["id"])
    pendientes = [d for d in deudas_c if d["estado"] == "pendiente"]
    if pendientes:
        total_pendiente = sum(d["monto"] for d in pendientes)
        clientes_con_deuda.append({
            "Cliente": c["nombre"],
            "Teléfono": c.get("telefono", ""),
            "Total Pendiente": f"${total_pendiente:,.2f}",
            "Cantidad de Deudas": len(pendientes)
        })

if clientes_con_deuda:
    df_resumen = pd.DataFrame(clientes_con_deuda)
    st.dataframe(df_resumen, use_container_width=True)
else:
    st.success("🎉 Ningún cliente tiene deudas pendientes.")

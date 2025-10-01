# frontend/pages/3_Pagos.py
import streamlit as st
import pandas as pd
from backend import clientes, deudas


st.markdown("""
<style>
.titulo-principal {font-size:2em; font-weight:bold; color:#2c3e50; margin-bottom:0.2em;}
.stButton>button {background-color:#27ae60; color:white; font-weight:bold; border-radius:6px;}
.stDataFrame {background-color:#f8f9fa;}
.alerta {color:#c0392b; font-weight:bold;}
</style>
""", unsafe_allow_html=True)
st.markdown('<div class="titulo-principal">💳 Pagos de Clientes</div>', unsafe_allow_html=True)

if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()

# ---------------------------
# CLIENTE INDIVIDUAL
# ---------------------------
clientes_data = clientes.list_clients()
clientes_dict = {c["nombre"]: c["id"] for c in clientes_data}


if not clientes_dict:
    st.warning("⚠️ No hay clientes registrados.")
else:
    colA, colB = st.columns([2,1])
    with colA:
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

            monto_max = next((d["monto"] for d in deudas_pendientes if d["id"] == deuda_id), 0)
            monto_pago = st.number_input("Monto a pagar", min_value=0.01, max_value=monto_max, step=0.01, help=f"Monto máximo: ${monto_max:,.2f}")
            if st.button("💾 Registrar Pago", help="Registrar el pago de la deuda seleccionada"):
                if monto_pago > monto_max:
                    st.error(f"El monto no puede ser mayor a la deuda (${monto_max:,.2f})")
                else:
                    updated = deudas.pay_debt(deuda_id, monto_pago)
                    st.success(
                        f"✅ Pago registrado. Estado deuda: **{updated['estado']}**, "
                        f"Monto restante: ${updated['monto']:,.2f}"
                    )
                    st.rerun()

# ---------------------------
# TABLA DE CLIENTES CON DEUDA
# ---------------------------

st.markdown('<div class="subtitulo">📊 Clientes con deuda pendiente</div>', unsafe_allow_html=True)

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

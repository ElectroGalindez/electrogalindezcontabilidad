if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()

import streamlit as st
import pandas as pd
from backend.clientes import list_clients, get_client
from backend.deudas import debts_by_client, pay_debt

st.title("💳 Gestión de Deudas y Pagos"
         )

clientes = list_clients()
clientes_con_deuda = [c for c in clientes if c.get("deuda_total", 0) > 0]
if not clientes_con_deuda:
    st.warning("No hay clientes con deuda pendiente.")
else:
    colA, colB = st.columns([2,1])
    with colA:
        cliente_str = st.selectbox("Seleccionar Cliente", [f"{c['id']} - {c['nombre']}" for c in clientes_con_deuda])
        cliente_id = cliente_str.split(" - ")[0]
        cliente_obj = get_client(cliente_id)

        st.markdown(f"<b>Deuda total actual:</b> <span style='color:#c0392b;'>${cliente_obj['deuda_total']:,.2f}</span>", unsafe_allow_html=True)



        # Historial de deudas individuales con botón mostrar/ocultar
        deudas_historial = debts_by_client(cliente_id)
        mostrar_historial = st.toggle("Mostrar historial de deudas", value=False)
        if mostrar_historial:
            if deudas_historial:
                df_deudas = pd.DataFrame(deudas_historial)
                df_deudas["monto"] = df_deudas["monto"].apply(lambda x: f"${x:,.2f}")
                st.markdown("<b>Historial de deudas:</b>", unsafe_allow_html=True)
                st.dataframe(df_deudas, use_container_width=True)
            else:
                st.info("Este cliente no tiene historial de deudas individuales.")

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<b>Registrar pago sobre una deuda individual:</b>", unsafe_allow_html=True)
        deudas_pendientes = [d for d in deudas_historial if d["estado"] == "pendiente" and d["monto"] > 0]
        if deudas_pendientes:
            deuda_ids = [d["id"] for d in deudas_pendientes]
            deuda_id = st.selectbox("Selecciona deuda a pagar", deuda_ids)
            monto_max = next((d["monto"] for d in deudas_pendientes if d["id"] == deuda_id), 0)
            monto_pago = st.number_input("Monto a pagar", min_value=0.00, max_value=monto_max, step=0.01, help=f"Monto máximo: ${monto_max:,.2f}")
            if st.button("Registrar Pago", help="Registrar pago sobre la deuda seleccionada"):
                if monto_pago > monto_max:
                    st.error(f"El monto no puede ser mayor a la deuda (${monto_max:,.2f})")
                else:
                    updated = pay_debt(deuda_id, monto_pago)
                    st.success(
                        f"✅ Pago registrado. Estado deuda: **{updated['estado']}**, "
                        f"Monto restante: ${updated['monto']:,.2f}"
                    )
                    st.rerun()
        else:
            st.info("No hay deudas pendientes para este cliente.")

# Tabla con todos los clientes con deudas
st.markdown("<hr>")
st.markdown("<b>Todos los clientes con deudas:</b>", unsafe_allow_html=True)
if clientes_con_deuda:
    import json
    # Cargar deudas para buscar la fecha de la primera deuda pendiente
    with open("../data/deudas.json", "r") as f:
        deudas_data = json.load(f)
    tabla_clientes = []
    for c in clientes_con_deuda:
        fechas = [d["fecha"] for d in deudas_data if d["cliente_id"] == c["id"] and d["estado"] == "pendiente"]
        fecha_deuda = min(fechas) if fechas else "-"
        tabla_clientes.append({
            "ID": c["id"],
            "Nombre": c["nombre"],
            "Teléfono": c.get("telefono", ""),
            "Deuda Total": f"${c['deuda_total']:,.2f}",
            "Desde": fecha_deuda
        })
    df_clientes = pd.DataFrame(tabla_clientes)
    st.dataframe(df_clientes, use_container_width=True)

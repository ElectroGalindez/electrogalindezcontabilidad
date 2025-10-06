import streamlit as st
import pandas as pd
from backend.clientes import list_clients, get_client
from backend.deudas import debts_by_client, pay_debt, list_debts

st.title("💳 Gestión de Deudas y Pagos")

# ---------------------------
# VERIFICAR SESIÓN
# ---------------------------
if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()

usuario_actual = st.session_state.usuario

# ---------------------------
# LISTA DE CLIENTES CON DEUDA
# ---------------------------
clientes = list_clients()
clientes_con_deuda = [c for c in clientes if c.get("deuda_total", 0) > 0]

if not clientes_con_deuda:
    st.warning("No hay clientes con deuda pendiente.")
else:
    colA, colB = st.columns([2, 1])
    with colA:
        cliente_str = st.selectbox(
            "Seleccionar Cliente",
            [f"{c.get('id', '')} - {c.get('nombre', '')}" for c in clientes_con_deuda]
        )
        cliente_id = cliente_str.split(" - ")[0]
        cliente_obj = get_client(cliente_id)

        deuda_total = cliente_obj.get("deuda_total", 0)
        st.markdown(
            f"<b>Deuda total actual:</b> "
            f"<span style='color:#c0392b;'>${deuda_total:,.2f}</span>",
            unsafe_allow_html=True
        )

        # ---------------------------
        # Historial de deudas individuales
        # ---------------------------
        deudas_historial = debts_by_client(cliente_id)
        mostrar_historial = st.toggle("📋 Mostrar historial de deudas", value=False)
        if mostrar_historial:
            if deudas_historial:
                df_deudas = pd.DataFrame(deudas_historial)
                df_deudas["fecha"] = pd.to_datetime(df_deudas["fecha"]).dt.strftime("%Y-%m-%d")
                df_deudas["monto_total"] = df_deudas["monto_total"].astype(float).round(2)
                st.dataframe(df_deudas, use_container_width=True)
            else:
                st.info("Este cliente no tiene historial de deudas.")

        st.divider()
        st.markdown("<b>💵 Registrar pago sobre una deuda:</b>", unsafe_allow_html=True)

        deudas_pendientes = [d for d in deudas_historial if d.get("estado") == "pendiente"]

        if deudas_pendientes:
            deuda_sel = st.selectbox(
                "Seleccionar deuda pendiente",
                [f"{d['id']} - ${d['monto_total']:,.2f}" for d in deudas_pendientes]
            )
            deuda_id = deuda_sel.split(" - ")[0]
            deuda_actual = next((d for d in deudas_pendientes if str(d["id"]) == deuda_id), None)

            monto_max = deuda_actual["monto_total"] if deuda_actual else 0
            monto_pago = st.number_input(
                "Monto a pagar", 0.00, monto_max, step=0.01,
                help=f"Monto máximo: ${monto_max:,.2f}"
            )

            if st.button("💰 Registrar Pago"):
                resultado = pay_debt(deuda_id, monto_pago, actor=usuario_actual)
                if "error" in resultado:
                    st.error(resultado["error"])
                else:
                    st.success(f"✅ Pago aplicado. Estado: {resultado['estado'].upper()} | Restante: ${resultado['monto_total']:,.2f}")
                    st.rerun()
        else:
            st.info("No hay deudas pendientes para este cliente.")

# ---------------------------
# TABLA GENERAL DE CLIENTES CON DEUDA
# ---------------------------
st.divider()
st.subheader("📊 Clientes con deudas pendientes")

deudas_todas = list_debts()
if not deudas_todas:
    st.info("No hay deudas registradas.")
else:
    resumen = []
    for cli in clientes_con_deuda:
        deudas_cli = [d for d in deudas_todas if d["cliente_id"] == cli["id"] and d["estado"] == "pendiente"]
        if not deudas_cli:
            continue
        total_cli = sum(float(d["monto_total"]) for d in deudas_cli)
        fecha_mas_antigua = min([d["fecha"] for d in deudas_cli])
        resumen.append({
            "Cliente": cli["nombre"],
            "Teléfono": cli.get("telefono", "-"),
            "Total Pendiente": f"${total_cli:,.2f}",
            "Desde": str(fecha_mas_antigua)
        })
    df_resumen = pd.DataFrame(resumen)
    st.dataframe(df_resumen, use_container_width=True)

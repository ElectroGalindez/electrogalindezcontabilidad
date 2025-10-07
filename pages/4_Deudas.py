import streamlit as st
import pandas as pd
from backend.clientes import list_clients, get_client
from backend.deudas import debts_by_client, pay_debt, list_debts

st.set_page_config(page_title="Deudas y Pagos", layout="wide")
st.title("💳 Gestión de Deudas y Pagos")

# ---------------------------
# Verificar sesión
# ---------------------------
if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()

usuario_actual = st.session_state.usuario["username"]

# ---------------------------
# Lista de clientes con deudas
# ---------------------------
clientes = list_clients()
clientes_con_deuda = [c for c in clientes if c.get("deuda_total", 0) > 0]

if not clientes_con_deuda:
    st.warning("No hay clientes con deuda pendiente.")
    st.stop()

# ---------------------------
# Selección de cliente
# ---------------------------
colA, colB = st.columns([2, 1])
with colA:
    cliente_sel = st.selectbox(
        "Seleccionar Cliente",
        [f"{c['id']} - {c['nombre']}" for c in clientes_con_deuda],
        key="cliente_con_deuda"
    )

    cliente_id = int(cliente_sel.split(" - ")[0])
    cliente_obj = get_client(cliente_id)
    deuda_total = float(cliente_obj.get("deuda_total", 0))

    st.markdown(
        f"<b>💰 Deuda total actual:</b> "
        f"<span style='color:#c0392b; font-size:18px;'>${deuda_total:,.2f}</span>",
        unsafe_allow_html=True
    )

    # ---------------------------
    # Historial de deudas
    # ---------------------------
    deudas_historial = debts_by_client(cliente_id)
    if st.checkbox("📋 Mostrar historial de deudas", value=True):
        if deudas_historial:
            df_hist = pd.DataFrame(deudas_historial)
            df_hist["fecha"] = pd.to_datetime(df_hist["fecha"]).dt.strftime("%Y-%m-%d")
            df_hist["monto_total"] = df_hist["monto_total"].astype(float).round(2)
            if "monto" in df_hist.columns:
                df_hist["pendiente"] = df_hist["monto"].astype(float).round(2)
            st.dataframe(
                df_hist[["id", "fecha", "monto_total", "pendiente", "estado"]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Este cliente no tiene historial de deudas.")

    st.divider()
    st.markdown("<b>💵 Registrar pago sobre una deuda:</b>", unsafe_allow_html=True)

    deudas_pendientes = [d for d in deudas_historial if d.get("estado") == "pendiente"]

    if deudas_pendientes:
        deuda_sel = st.selectbox(
            "Seleccionar deuda pendiente",
            [f"{d['id']} - ${float(d['monto']):,.2f}" for d in deudas_pendientes],
            key="deuda_sel"
        )

        deuda_id = int(deuda_sel.split(" - ")[0])
        deuda_actual = next((d for d in deudas_pendientes if int(d["id"]) == deuda_id), None)

        monto_max = float(deuda_actual["monto"])
        monto_pago = st.number_input(
            "Monto a pagar", 0.0, monto_max, step=0.01,
            help=f"Monto máximo: ${monto_max:,.2f}"
        )

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("💰 Registrar Pago"):
                try:
                    resultado = pay_debt(deuda_id, monto_pago, usuario=usuario_actual)
                    if not resultado:
                        st.error("No se pudo registrar el pago. Verifica la deuda seleccionada.")
                    else:
                        estado_final = resultado.get("estado", "desconocido").capitalize()
                        restante = resultado.get("monto", 0.0)
                        st.success(
                            f"✅ Pago registrado correctamente. Estado final: {estado_final} | Restante: ${restante:,.2f}"
                        )
                        st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error al registrar pago: {str(e)}")

        with col2:
            if st.button("🧹 Vaciar selección"):
                st.session_state.pop("deuda_sel", None)
                st.experimental_rerun()

    else:
        st.info("No hay deudas pendientes para este cliente.")

# ---------------------------
# Resumen general de clientes con deudas pendientes
# ---------------------------
st.divider()
st.subheader("📊 Resumen de Clientes con Deudas Pendientes")

deudas_todas = list_debts()
resumen = []
for cli in clientes_con_deuda:
    deudas_cli = [
        d for d in deudas_todas if d["cliente_id"] == cli["id"] and d["estado"] == "pendiente"
    ]
    if not deudas_cli:
        continue
    total_cli = sum(float(d["monto"]) for d in deudas_cli)
    fecha_mas_antigua = min(pd.to_datetime(d["fecha"]) for d in deudas_cli)
    resumen.append({
        "Cliente": cli["nombre"],
        "Teléfono": cli.get("telefono", "-"),
        "Total Pendiente": total_cli,
        "Desde": fecha_mas_antigua.date()
    })

if resumen:
    df_resumen = pd.DataFrame(resumen).sort_values("Total Pendiente", ascending=False)
    df_resumen["Total Pendiente"] = df_resumen["Total Pendiente"].apply(lambda x: f"${x:,.2f}")
    st.dataframe(df_resumen, use_container_width=True)
else:
    st.info("No hay deudas pendientes registradas.")

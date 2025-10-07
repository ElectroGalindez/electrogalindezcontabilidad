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

            # Calcular campo "pendiente" de forma segura
            if "monto" in df_hist.columns:
                # Caso de versiones anteriores con columna monto
                df_hist["pendiente"] = df_hist["monto"].astype(float).round(2)
            else:
                # Si no hay columna "monto", usamos monto_total si el estado es pendiente
                df_hist["pendiente"] = df_hist.apply(
                    lambda r: r["monto_total"] if r["estado"] == "pendiente" else 0.0,
                    axis=1
                )

        # Mostrar solo las columnas existentes
        columnas_a_mostrar = [c for c in ["id", "fecha", "monto_total", "pendiente", "estado"] if c in df_hist.columns]
        st.dataframe(df_hist[columnas_a_mostrar], use_container_width=True, hide_index=True)
    else:
        st.info("Este cliente no tiene historial de deudas.")

   
st.divider()
st.markdown("<b>💵 Registrar pago sobre una deuda:</b>", unsafe_allow_html=True)

# 🔸 Obtener solo deudas pendientes
deudas_pendientes = [d for d in deudas_historial if str(d.get("estado", "")).lower() == "pendiente"]

if deudas_pendientes:
    # Función auxiliar para obtener el monto correctamente
    def obtener_monto(d):
        valor = d.get("monto", d.get("monto_total", 0))
        try:
            return float(valor)
        except Exception:
            return 0.0

    # Construir lista de opciones para el selectbox
    opciones = [
        f"{d['id']} - ${obtener_monto(d):,.2f}"
        for d in deudas_pendientes
    ]

    deuda_sel = st.selectbox("Seleccionar deuda pendiente", opciones, key="deuda_sel")

    deuda_id = int(deuda_sel.split(" - ")[0])
    deuda_actual = next((d for d in deudas_pendientes if int(d["id"]) == deuda_id), None)

    monto_max = obtener_monto(deuda_actual)
    monto_pago = st.number_input(
        "Monto a pagar",
        min_value=0.0,
        max_value=monto_max,
        step=0.01,
        help=f"Monto máximo: ${monto_max:,.2f}",
        key="monto_pago"
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
                    restante = float(resultado.get("monto", resultado.get("monto_total", 0.0)))
                    st.success(
                        f"✅ Pago registrado correctamente. "
                        f"Estado final: {estado_final} | Restante: ${restante:,.2f}"
                    )
                    st.status()
            except Exception as e:
                st.error(f"Error al registrar pago: {str(e)}")

    with col2:
        if st.button("🧹 Vaciar selección"):
            st.session_state.pop("deuda_sel", None)
            st.status()

else:
    st.info("No hay deudas pendientes para este cliente.")

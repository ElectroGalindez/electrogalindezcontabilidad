import streamlit as st
import pandas as pd
from backend.clientes import list_clients, get_client
from backend.deudas import debts_by_client, pay_debt

st.set_page_config(page_title="Deudas y Pagos", layout="wide")
st.title("💳 Gestión de Deudas y Pagos")

# ---------------------------
# Función auxiliar para convertir a float de forma segura
# ---------------------------
def to_float(valor, default=0.0):
    try:
        return float(valor)
    except Exception:
        return default

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
clientes = list_clients() or []
clientes_con_deuda = [c for c in clientes if to_float(c.get("deuda_total", 0)) > 0]

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
    cliente_obj = get_client(cliente_id) or {}
    deuda_total = to_float(cliente_obj.get("deuda_total", 0.0))

    st.markdown(
        f"<b>💰 Deuda total actual:</b> "
        f"<span style='color:#c0392b; font-size:18px;'>${deuda_total:,.2f}</span>",
        unsafe_allow_html=True
    )

    # ---------------------------
    # Historial de deudas
    # ---------------------------
    deudas_historial = debts_by_client(cliente_id) or []
    if deudas_historial and st.checkbox("📋 Mostrar historial de deudas", value=True):
        df_hist = pd.DataFrame(deudas_historial)
        if not df_hist.empty:
            df_hist["fecha"] = pd.to_datetime(df_hist["fecha"], errors='coerce').dt.strftime("%Y-%m-%d")
            df_hist["monto_total"] = df_hist.get("monto_total", 0.0).apply(to_float)
            df_hist["pendiente"] = df_hist.apply(
                lambda r: to_float(r.get("monto", r.get("monto_total", 0.0)))
                if str(r.get("estado","")).lower() == "pendiente" else 0.0,
                axis=1
            )
            columnas_a_mostrar = [c for c in ["id","fecha","monto_total","pendiente","estado"] if c in df_hist.columns]
            st.dataframe(df_hist[columnas_a_mostrar].style.format({
                "monto_total": "${:,.2f}", "pendiente": "${:,.2f}"
            }).applymap(lambda v: 'color: red;' if isinstance(v,float) and v>0 else '', subset=["pendiente"]),
            use_container_width=True)
    elif not deudas_historial:
        st.info("Este cliente no tiene historial de deudas.")

st.divider()
st.markdown("<b>💵 Registrar pago sobre una deuda:</b>", unsafe_allow_html=True)

# ---------------------------
# Deudas pendientes
# ---------------------------
deudas_pendientes = [d for d in deudas_historial if str(d.get("estado","")).lower() == "pendiente"]

if deudas_pendientes:
    # Selección de deuda y monto
    def monto_valido(d): return to_float(d.get("monto", d.get("monto_total", 0.0)))
    opciones = [f"{d['id']} - ${monto_valido(d):,.2f}" for d in deudas_pendientes]
    deuda_sel = st.selectbox("Seleccionar deuda pendiente", opciones, key="deuda_sel")
    deuda_id = int(deuda_sel.split(" - ")[0])
    deuda_actual = next((d for d in deudas_pendientes if int(d["id"]) == deuda_id), None)
    monto_max = monto_valido(deuda_actual)
    
    monto_pago = st.number_input(
        "Monto a pagar",
        min_value=0.0,
        max_value=monto_max,
        step=0.01,
        value=min(0.0, monto_max),
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
                    restante = to_float(resultado.get("monto", resultado.get("monto_total", 0.0)))
                    st.success(
                        f"✅ Pago registrado correctamente. "
                        f"Estado final: {estado_final} | Restante: ${restante:,.2f}"
                    )
                    st.experimental_rerun()
            except Exception as e:
                st.error(f"Error al registrar pago: {str(e)}")

    with col2:
        if st.button("🧹 Vaciar selección"):
            for key in ["deuda_sel", "monto_pago"]:
                if key in st.session_state:
                    st.session_state.pop(key)
            st.experimental_rerun()
else:
    st.info("No hay deudas pendientes para este cliente.")

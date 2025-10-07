import streamlit as st
import pandas as pd
from backend.clientes import list_clients, get_client
from backend.deudas import debts_by_client, pay_debt

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
# Cache de clientes con TTL
# ---------------------------
@st.cache_data(ttl=10)
def cached_clients():
    return list_clients()

clientes_data = cached_clients()

# ---------------------------
# Clientes con deuda
# ---------------------------
clientes_con_deuda = [c for c in clientes_data if float(c.get("deuda_total", 0)) > 0]

if not clientes_con_deuda:
    st.info("No hay clientes con deuda pendiente.")
    st.stop()

# ---------------------------
# Selector de cliente
# ---------------------------
cliente_opciones = [f"{c['id']} - {c['nombre']}" for c in clientes_con_deuda]
cliente_sel = st.selectbox("Seleccionar Cliente", cliente_opciones, key="cliente_sel")
cliente_id = int(cliente_sel.split(" - ")[0])
cliente_obj = get_client(cliente_id)
deuda_total = float(cliente_obj.get("deuda_total", 0.0))

st.markdown(
    f"<b>💰 Deuda total actual:</b> "
    f"<span style='color:#c0392b; font-size:18px;'>${deuda_total:,.2f}</span>",
    unsafe_allow_html=True
)

# ---------------------------
# Historial de deudas
# ---------------------------
deudas_historial = debts_by_client(cliente_id) or []

if deudas_historial:
    if st.checkbox("📋 Mostrar historial de deudas", value=True):
        df_hist = pd.DataFrame(deudas_historial)
        if not df_hist.empty:
            df_hist["fecha"] = pd.to_datetime(df_hist["fecha"], errors='coerce').dt.strftime("%Y-%m-%d")
            df_hist["monto_total"] = df_hist.get("monto_total", 0.0).astype(float)
            df_hist["pendiente"] = df_hist.apply(
                lambda r: float(r.get("monto", r.get("monto_total", 0.0))) 
                if str(r.get("estado","")).lower() == "pendiente" else 0.0,
                axis=1
            )
            columnas_mostrar = [c for c in ["id","fecha","monto_total","pendiente","estado"] if c in df_hist.columns]
            st.dataframe(
                df_hist[columnas_mostrar].style.format({"monto_total":"${:,.2f}","pendiente":"${:,.2f}"})
                .applymap(lambda v: 'color: red;' if isinstance(v,float) and v>0 else '', subset=["pendiente"]),
                use_container_width=True
            )
else:
    st.info("Este cliente no tiene historial de deudas.")

st.divider()
st.markdown("<b>💵 Registrar pago:</b>", unsafe_allow_html=True)

# ---------------------------
# Deudas pendientes
# ---------------------------
deudas_pendientes = [d for d in deudas_historial if str(d.get("estado","")).lower() == "pendiente"]

if deudas_pendientes:
    # Selector de deuda
    opciones_deudas = [f"{d['id']} - ${float(d.get('monto', d.get('monto_total',0))):,.2f}" for d in deudas_pendientes]
    deuda_sel = st.selectbox("Seleccionar deuda pendiente", opciones_deudas, key="deuda_sel")
    deuda_id = int(deuda_sel.split(" - ")[0])
    deuda_actual = next((d for d in deudas_pendientes if int(d["id"]) == deuda_id), None)
    monto_max = float(deuda_actual.get("monto", deuda_actual.get("monto_total",0.0)))

    # Monto a pagar
    monto_pago = st.number_input(
        "Monto a pagar",
        min_value=0.0,
        max_value=monto_max,
        step=0.01,
        value=monto_max,
        key="monto_pago"
    )

    if st.button("💰 Registrar Pago"):
        try:
            resultado = pay_debt(deuda_id, monto_pago, usuario=usuario_actual)
            if resultado:
                estado_final = resultado.get("estado", "desconocido").capitalize()
                restante = float(resultado.get("monto", resultado.get("monto_total",0.0)))
                st.success(f"✅ Pago registrado. Estado final: {estado_final} | Restante: ${restante:,.2f}")
                st.experimental_rerun()
            else:
                st.error("❌ No se pudo registrar el pago. Verifica la deuda seleccionada.")
        except Exception as e:
            st.error(f"❌ Error al registrar pago: {str(e)}")
else:
    st.info("No hay deudas pendientes para este cliente.")

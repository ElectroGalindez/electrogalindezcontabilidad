import streamlit as st
import pandas as pd
from io import BytesIO
from backend import clientes, productos, deudas


if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()


# ==========================================================
# CACHÉ — OPTIMIZACIÓN CRÍTICA
# ==========================================================
@st.cache_data(ttl=30)
def load_clientes_con_deuda():
    return deudas.list_clientes_con_deuda() or []

@st.cache_data(ttl=30)
def load_productos_map():
    return productos.map_productos() or {}

@st.cache_data(ttl=10)
def load_deudas_cliente(cid: int):
    return deudas.debts_by_client(cid) or []

@st.cache_data(ttl=20)
def load_detalle_deudas():
    # Recomendación: en backend filtrar solo pendientes para acelerar aún más
    return deudas.list_detalle_deudas() or []

@st.cache_data(ttl=30)
def load_clientes_dict():
    lista = clientes.list_clients() or []
    return {c["id"]: c["nombre"] for c in lista}



# ==========================================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================================
st.set_page_config(page_title="💳 Gestión de Deudas", layout="wide")
st.title("💳 Gestión de Deudas")



# ==========================================================
# CARGAR DATOS
# ==========================================================
clientes_con_deuda = load_clientes_con_deuda()
productos_map = load_productos_map()
clientes_dict = load_clientes_dict()

clientes_opciones = {c["nombre"]: c["id"] for c in clientes_con_deuda}
lista_nombres = [""] + list(clientes_opciones.keys())



# ==========================================================
# SELECTOR DE CLIENTE
# ==========================================================
st.subheader("👤 Seleccionar Cliente")
cliente_sel = st.selectbox(
    "Buscar cliente por nombre",
    lista_nombres,
    index=0,
    key="cliente_selector",
)

cliente_id = clientes_opciones.get(cliente_sel)


# ==========================================================
# 📋 BLOQUE DE DEUDAS PENDIENTES DEL CLIENTE
# ==========================================================
if cliente_sel and cliente_id:

    cliente_obj = clientes.get_client(cliente_id)
    deuda_total = float(cliente_obj.get("deuda_total", 0) or 0)

    st.markdown(
        f"<h4>💰 Deuda total de {cliente_sel}: "
        f"<span style='color:#c0392b;'>${deuda_total:,.2f}</span></h4>",
        unsafe_allow_html=True
    )

    # Cargar deudas del cliente
    deudas_cliente = load_deudas_cliente(cliente_id)

    filas_pendientes = []
    for deuda in deudas_cliente:
        for det in deuda.get("detalles", []):
            if (det.get("estado") or "").lower() != "pendiente":
                continue

            cantidad = float(det.get("cantidad") or 0)
            precio_unitario = float(det.get("precio_unitario") or 0)
            monto_pendiente = cantidad * precio_unitario

            filas_pendientes.append({
                "deuda_id": deuda.get("deuda_id"),
                "Detalle ID": det.get("id"),
                "Producto ID": det.get("producto_id"),
                "Producto": productos_map.get(det.get("producto_id"), "Producto"),
                "Cantidad": cantidad,
                "Precio Unitario": round(precio_unitario, 2),
                "Monto Pendiente": round(monto_pendiente, 2),
                "Fecha": str(deuda.get("fecha"))[:19],
            })

    df_pendientes = pd.DataFrame(filas_pendientes)

    st.subheader("📋 Deudas Pendientes del Cliente")

    if df_pendientes.empty:
        st.info("✔ Este cliente no tiene deudas pendientes.")
    else:
        # Mostrar tabla de deudas
        st.dataframe(
            df_pendientes[["Producto","Cantidad", "Precio Unitario", "Monto Pendiente", "Fecha"]]
            .sort_values("Fecha", ascending=False)
            .style.format({
                "Cantidad": "{:,.0f}",
                "Precio Unitario": "${:,.2f}",
                "Monto Pendiente": "${:,.2f}"
            }),
            use_container_width=True,
            height=200
        )

        # -----------------------------
        # Selector de deuda a pagar
        # -----------------------------
        opciones_deuda = {
            f"{row['Producto']} - {row['Fecha']} (${row['Monto Pendiente']:,.2f})": row
            for _, row in df_pendientes.iterrows()
        }

        seleccion_detalle = st.selectbox(
            "Selecciona la deuda a rebajar",
            [""] + list(opciones_deuda.keys()),
            index=0
        )

        if seleccion_detalle:
            detalle = opciones_deuda[seleccion_detalle]
            monto_actual = detalle["Monto Pendiente"]
            detalle_id = detalle["Detalle ID"]

            st.markdown(f"### 💵 Monto pendiente de la deuda: **${monto_actual:,.2f}**")

            # -----------------------------
            # Input monto a pagar
            # -----------------------------
            monto_pago = st.number_input(
                "Monto a pagar",
                min_value=0.01,
                max_value=monto_actual,
                value=monto_actual,
                step=0.01,
                key=f"monto_pago_{detalle_id}"
            )

            # -----------------------------
            # Botón registrar pago + generar PDF
            # -----------------------------
            if st.button(f"Registrar pago y generar factura (${monto_pago:,.2f})", key=f"btn_pagar_{detalle_id}"):
                try:
                    # Registrar pago
                    resultado = deudas.pay_debt_producto(
                        deuda_id=detalle["deuda_id"],
                        producto_id=detalle["Producto ID"],
                        monto_pago=monto_pago,
                        usuario=st.session_state.get("usuario", "desconocido")
                    )
                    st.success(f"💰 Pago de ${monto_pago:,.2f} registrado correctamente.")

                    # -----------------------------
                    # Generar PDF doble
                    # -----------------------------
                    from backend.deudas import generar_factura_pago_deuda

                    detalle_factura = [{
                        "nombre": detalle["Producto"],
                        "cantidad": round(monto_pago / detalle.get("Precio Unitario", 1), 2),
                        "precio_unitario": detalle.get("Precio Unitario", 1)
                    }]

                    pdf_bytes = generar_factura_pago_deuda(cliente_obj, detalle_factura)

                    st.download_button(
                        label="⬇️ Descargar Comprobante de Pago",
                        data=pdf_bytes,
                        file_name=f"ComprobantePago_{detalle['deuda_id']}_{detalle['producto_id']}.pdf",
                        mime="application/pdf"
                    )

                    # Limpiar cache y recargar
                    st.cache_data.clear()
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Error al registrar el pago: {str(e)}")

# ==========================================================
# TABLA GENERAL DE TODAS LAS DEUDAS PENDIENTES
# ==========================================================
st.subheader("📊 Todas las Deudas Pendientes")

detalles_totales = load_detalle_deudas()
filas = []

for d in detalles_totales:
    if str(d.get("estado", "pendiente")).lower() != "pendiente":
        continue

    cantidad = float(d.get("cantidad") or 0)
    precio_unitario = float(d.get("precio_unitario") or 0)
    monto_total = cantidad * precio_unitario

    filas.append({
        "Cliente": clientes_dict.get(d.get("cliente_id"), "Desconocido"),
        "Deuda ID": d.get("deuda_id"),
        "Producto": productos_map.get(d.get("producto_id"), "Producto"),
        "Cantidad": round(cantidad, 2),
        "Precio Unitario": round(precio_unitario, 2),
        "Monto Total": round(monto_total, 2),
        "Fecha": str(d.get("fecha"))[:19]
    })

df_general = pd.DataFrame(filas)

if df_general.empty:
    st.info("✔ No hay deudas pendientes.")
else:
    st.dataframe(
        df_general.sort_values(["Fecha", "Cliente"], ascending=[False, True])
        .style.format({
            "Cantidad": "{:,.0f}",
            "Precio Unitario": "${:,.2f}",
            "Monto Total": "${:,.2f}"
        }),
        use_container_width=True,
        height=400
    )

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df_general.to_excel(writer, index=False, sheet_name="DeudasPendientes")

    st.download_button(
        "⬇️ Descargar Excel General",
        buffer.getvalue(),
        "deudas_pendientes.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

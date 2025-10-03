# frontend/pages/5_Deudas.py
import streamlit as st
import pandas as pd
from backend.clientes import list_clients, get_client
from backend.deudas import debts_by_client, pay_debt
import json

st.title("💳 Gestión de Deudas y Pagos")

# ---------------------------
# VERIFICAR SESIÓN
# ---------------------------
if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()

# ---------------------------
# LISTA DE CLIENTES CON DEUDA
# ---------------------------
clientes = list_clients()
clientes_con_deuda = [c for c in clientes if c.get("deuda_total", 0) > 0]

if not clientes_con_deuda:
    st.warning("No hay clientes con deuda pendiente.")
else:
    colA, colB = st.columns([2,1])
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
        mostrar_historial = st.toggle("Mostrar historial de deudas", value=False)
        if mostrar_historial:
            if deudas_historial:
                df_deudas = pd.DataFrame(deudas_historial)

                # Asegurar columna 'monto_total'
                if "monto_total" not in df_deudas.columns:
                    df_deudas["monto_total"] = df_deudas.apply(lambda x: x.get("monto", 0), axis=1)

                # Formatear montos
                df_deudas["monto_total"] = df_deudas["monto_total"].apply(lambda x: f"${x:,.2f}" if x else "$0.00")
                
                st.markdown("<b>Historial de deudas:</b>", unsafe_allow_html=True)
                st.dataframe(df_deudas, use_container_width=True)
            else:
                st.info("Este cliente no tiene historial de deudas individuales.")

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<b>Registrar pago sobre una deuda individual:</b>", unsafe_allow_html=True)

        # Filtrar deudas pendientes
        deudas_pendientes = [
            d for d in deudas_historial
            if d.get("estado") == "pendiente" and d.get("monto_total", d.get("monto", 0)) > 0
        ]

        if deudas_pendientes:
            deuda_ids = [d.get("id") for d in deudas_pendientes]
            deuda_id = st.selectbox("Selecciona deuda a pagar", deuda_ids)
            
            # Monto máximo disponible
            monto_max = next(
                (d.get("monto_total", d.get("monto", 0)) for d in deudas_pendientes if d.get("id") == deuda_id),
                0
            )

            monto_pago = st.number_input(
                "Monto a pagar",
                min_value=0.00,
                max_value=monto_max,
                step=0.01,
                help=f"Monto máximo: ${monto_max:,.2f}"
            )
            if st.button("Registrar Pago", help="Registrar pago sobre la deuda seleccionada"):
                if monto_pago > monto_max:
                    st.error(f"El monto no puede ser mayor a la deuda (${monto_max:,.2f})")
                else:
                    updated = pay_debt(deuda_id, monto_pago)
                    st.success(
                        f"✅ Pago registrado. Estado deuda: **{updated.get('estado', '')}**, "
                        f"Monto restante: ${updated.get('monto_total', updated.get('monto',0)):,.2f}"
                    )
                    st.rerun()
        else:
            st.info("No hay deudas pendientes para este cliente.")

# ---------------------------
# TABLA GENERAL DE CLIENTES CON DEUDA
# ---------------------------
st.markdown("<b>Todos los clientes con deudas:</b>", unsafe_allow_html=True)

if clientes_con_deuda:
    # Cargar deudas
    with open("./data/deudas.json", "r", encoding="utf-8") as f:
        deudas_data = json.load(f)

    tabla_clientes = []
    for c in clientes_con_deuda:
        deudas_cliente = [
            d for d in deudas_data
            if d.get("cliente_id") == c.get("id") and d.get("estado") == "pendiente"
        ]

        # Fecha más antigua de deuda
        fechas = [d.get("fecha", "") for d in deudas_cliente]
        fecha_deuda = min(fechas) if fechas else "-"

        # Listar productos involucrados
        productos_deuda = []
        for d in deudas_cliente:
            for p in d.get("productos", []):
                nombre = p.get("nombre", "Desconocido")
                cantidad = p.get("cantidad", 1)
                productos_deuda.append(f"{nombre} (x{cantidad})")
        productos_texto = ", ".join(productos_deuda) if productos_deuda else "-"

        # Calcular deuda total
        deuda_total_cliente = sum(d.get("monto_total", d.get("monto", 0)) for d in deudas_cliente)

        tabla_clientes.append({
            "ID": c.get("id", ""),
            "Nombre": c.get("nombre", ""),
            "Teléfono": c.get("telefono", ""),
            "Deuda Total": f"${deuda_total_cliente:,.2f}",
            "Desde": fecha_deuda,
            "Productos": productos_texto
        })

    df_clientes = pd.DataFrame(tabla_clientes)
    st.dataframe(df_clientes, use_container_width=True)

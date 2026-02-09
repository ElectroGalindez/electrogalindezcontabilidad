import streamlit as st
import pandas as pd
from backend import productos, clientes, ventas
from backend.deudas import add_debt
from datetime import datetime


def render() -> None:
    st.set_page_config(page_title="Ventas Profesionales", layout="wide")
    st.title("🛒 Registrar Venta Profesional")

    # ---------------------------
    # Verificar sesión
    # ---------------------------
    if "usuario" not in st.session_state or st.session_state.usuario is None:
        st.warning("Debes iniciar sesión para acceder a esta página.")
        st.stop()

    usuario_actual = st.session_state.usuario["username"]

    # ---------------------------
    # Cache eficiente para clientes y productos
    # ---------------------------
    @st.cache_data(ttl=20)
    def cached_clients():
        return clientes.list_clients() or []

    @st.cache_data(ttl=20)
    def cached_products():
        return productos.list_products() or []

    clientes_data = cached_clients()
    productos_data = cached_products()

    clientes_dict = {c["nombre"]: c["id"] for c in clientes_data}

    # ---------------------------
    # 👤 Selección de cliente
    # ---------------------------
    st.subheader("Cliente")
    cliente_id = None
    cliente_nombre = st.selectbox(
        "Selecciona un cliente existente",
        [""] + list(clientes_dict.keys()),
        key="select_cliente_ventas"
    )
    if cliente_nombre:
        cliente_id = clientes_dict[cliente_nombre]

    # ---------------------------
    # ➕ Crear nuevo cliente
    # ---------------------------
    with st.expander("➕ Crear nuevo cliente", expanded=False):
        with st.form("form_nuevo_cliente", clear_on_submit=True):
            nombre_nuevo = st.text_input("Nombre *")
            direccion_nueva = st.text_input("Dirección")
            telefono_nuevo = st.text_input("Teléfono")
            ci_nuevo = st.text_input("CI")
            chapa_nueva = st.text_input("Chapa")

            if st.form_submit_button("Crear cliente"):
                if not nombre_nuevo.strip():
                    st.error("❌ El nombre no puede estar vacío.")
                else:
                    clientes.add_client(
                        nombre=nombre_nuevo,
                        direccion=direccion_nueva,
                        telefono=telefono_nuevo,
                        ci=ci_nuevo,
                        chapa=chapa_nueva
                    )
                    st.success(f"✅ Cliente '{nombre_nuevo}' creado correctamente.")
                    st.cache_data.clear()  # limpiar cache
                    st.rerun()

    # ---------------------------
    # 📦 Selección de productos
    # ---------------------------
    if "items_venta" not in st.session_state:
        st.session_state["items_venta"] = []

    st.subheader("Productos disponibles")
    if productos_data:
        opciones = {f"{p['nombre']} (Stock: {p['cantidad']}, ${p['precio']:.2f})": p for p in productos_data}
        producto_nombre = st.selectbox("Selecciona un producto", [""] + list(opciones.keys()), key="select_producto_ventas")

        if producto_nombre:
            prod = opciones[producto_nombre]
            cantidad = st.number_input("Cantidad", min_value=1, max_value=prod["cantidad"], value=1, key=f"cant_{prod['id']}")
            precio = st.number_input("Precio unitario", min_value=0.01, value=float(prod["precio"]), step=0.01, key=f"precio_{prod['id']}")

            if st.button(f"➕ Añadir {prod['nombre']}", key=f"add_{prod['id']}"):
                existente = next((i for i in st.session_state["items_venta"] if i["id_producto"] == prod["id"]), None)
                if existente:
                    total_cantidad = existente["cantidad"] + cantidad
                    if total_cantidad > prod["cantidad"]:
                        st.error(f"Stock insuficiente ({prod['cantidad']} disponible)")
                    else:
                        existente["cantidad"] = total_cantidad
                        existente["precio_unitario"] = precio
                        st.success(f"Cantidad de {prod['nombre']} actualizada ✅")
                else:
                    st.session_state["items_venta"].append({
                        "id_producto": prod["id"],
                        "nombre": prod["nombre"],
                        "cantidad": cantidad,
                        "precio_unitario": precio
                    })
                    st.success(f"Producto {prod['nombre']} agregado ✅")
    else:
        st.warning("No hay productos registrados en el inventario.")

    # ---------------------------
    # 📝 Orden actual
    # ---------------------------
    if st.session_state["items_venta"]:
        st.subheader("Orden actual")
        df = pd.DataFrame(st.session_state["items_venta"])
        df["Subtotal"] = df["cantidad"] * df["precio_unitario"]

        moneda_cols = ["precio_unitario", "Subtotal"]
        df_display = df.copy()
        for col in moneda_cols:
            df_display[col] = df_display[col].map("${:,.2f}".format)

        st.dataframe(df_display[["id_producto", "nombre", "cantidad", "precio_unitario", "Subtotal"]], use_container_width=True)

        total = df["Subtotal"].sum()
        st.subheader(f"💰 Total: ${total:,.2f}")

        col_a, col_b = st.columns([1, 1])
        with col_a:
            if st.button("🗑️ Vaciar orden", key="vaciar_orden"):
                st.session_state["items_venta"] = []
                st.success("🧹 Orden vaciada correctamente.")
                st.rerun()

        with col_b:
            if cliente_id:
                pago_estado = st.radio("Estado del pago", ["Pagado", "Pendiente"])
                tipo_pago = st.selectbox("Método de pago", ["Efectivo", "Transferencia", "Tarjeta", "Otro"], key="tipo_pago_venta") if pago_estado == "Pagado" else "Pendiente"

                if st.button("💾 Registrar Venta", key="registrar_venta"):
                    if not st.session_state["items_venta"]:
                        st.error("No hay productos en la venta.")
                    else:
                        try:
                            monto_pagado = float(total) if pago_estado == "Pagado" else 0.0
                            nueva_venta = ventas.register_sale(
                                cliente_id=cliente_id,
                                productos=st.session_state["items_venta"],
                                total=float(total),
                                pagado=monto_pagado,
                                usuario=usuario_actual,
                                tipo_pago=tipo_pago
                            )

                            if pago_estado == "Pendiente":
                                saldo_pendiente = float(total) - monto_pagado
                                add_debt(
                                    cliente_id=cliente_id,
                                    monto_total=saldo_pendiente,
                                    venta_id=nueva_venta["id"],
                                    productos=st.session_state["items_venta"],
                                    usuario=usuario_actual,
                                    estado="pendiente"
                                )
                                st.info(f"Deuda creada por ${saldo_pendiente:,.2f}")

                            st.success(f"✅ Venta registrada ID {nueva_venta['id']} - Total ${nueva_venta['total']:.2f}")
                            st.session_state["items_venta"] = []
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al registrar la venta: {str(e)}")

    st.markdown("---")
    st.title("💳 Generar Factura Profesional en PDF")

    ventas_list = ventas.list_sales()

    if "ventas_count" not in st.session_state:
        st.session_state.ventas_count = len(ventas_list)

    if len(ventas_list) != st.session_state.ventas_count:
        st.session_state.ventas_dict = None
        st.session_state.ventas_count = len(ventas_list)

    if "ventas_dict" not in st.session_state or st.session_state.ventas_dict is None:
        st.session_state.ventas_dict = {
            f"ID {v['id']} - Cliente {v.get('cliente_id','N/A')} - Total ${v.get('total', 0):.2f}": v
            for v in ventas_list
        }

    venta_keys = [""] + list(st.session_state.ventas_dict.keys())
    venta_sel = st.selectbox("Selecciona venta", venta_keys)

    if not venta_sel:
        st.stop()

    venta_obj = st.session_state.ventas_dict[venta_sel]
    cliente_obj = clientes.get_client(venta_obj.get("cliente_id"))

    if not cliente_obj:
        st.error(f"❌ No se encontró el cliente con ID {venta_obj.get('cliente_id')}")
        st.stop()

    productos_vendidos = venta_obj.get("productos_vendidos", [])

    with st.form("form_datos_factura"):
        st.subheader("✏️ Datos adicionales (solo para la factura)")

        observaciones = st.text_area("Observaciones", value=venta_obj.get("observaciones", ""))

        col1, col2 = st.columns(2)
        with col1:
            vendedor = st.text_input("Vendedor", value=venta_obj.get("vendedor", ""))
            chofer = st.text_input("Chofer", value=venta_obj.get("chofer", ""))
        with col2:
            telefono_vendedor = st.text_input("Teléfono del Vendedor", value=venta_obj.get("telefono_vendedor", ""))
            chapa = st.text_input("Chapa", value=venta_obj.get("chapa", ""))

        generar_y_descargar = st.form_submit_button("🖨️ Generar y Descargar Factura PDF")

    if generar_y_descargar:
        venta_obj["observaciones"] = observaciones
        venta_obj["vendedor"] = vendedor
        venta_obj["telefono_vendedor"] = telefono_vendedor
        venta_obj["chofer"] = chofer
        venta_obj["chapa"] = chapa

        st.session_state.ventas_dict[venta_sel] = venta_obj

        gestor_info = {
            "vendedor": f"{vendedor} (+53 {telefono_vendedor})" if vendedor else "",
            "chofer": chofer,
            "chapa": chapa
        }

        pdf_bytes = ventas.generar_factura_pdf(
            venta_obj,
            cliente_obj,
            productos_vendidos,
            gestor_info=gestor_info,
            logo_path="assets/logo.png"
        )

        st.download_button(
            label=f"⬇️ Descargar Factura PDF {venta_obj.get('id')}",
            data=pdf_bytes,
            file_name=f"Factura_{venta_obj.get('id')}.pdf",
            mime="application/pdf"
        )
        st.success("Factura generada y lista para descargar ✔")

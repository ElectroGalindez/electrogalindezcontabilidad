import streamlit as st
import pandas as pd
from datetime import datetime
import json
from backend import productos, clientes, ventas
from backend.deudas import add_debt 


st.set_page_config(page_title="Ventas", layout="wide")
st.title("🛒 Registrar Venta")

# ---------------------------
# Verificar sesión
# ---------------------------
if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()

# ---------------------------
# Cliente
# ---------------------------
st.subheader("👤 Cliente")
clientes_data = clientes.list_clients()
clientes_dict = {c["nombre"]: c["id"] for c in clientes_data}
cliente_id = None

# Selección de cliente existente
if clientes_dict:
    cliente_nombre = st.selectbox(
        "Selecciona un cliente existente",
        [""] + list(clientes_dict.keys()),
        key="select_cliente_ventas"
    )

    if cliente_nombre:
        cliente_id = clientes_dict[cliente_nombre]

# Crear nuevo cliente
with st.expander("➕ Agregar nuevo cliente"):
    with st.form("form_nuevo_cliente", clear_on_submit=True):
        nombre_nuevo = st.text_input("Nombre del cliente")
        telefono_nuevo = st.text_input("Teléfono")
        ci_nuevo = st.text_input("C.I.")
        chapa_nueva = st.text_input("Chapa")
        direccion_nueva = st.text_input("Dirección")
        submitted = st.form_submit_button("Guardar Cliente")
        if submitted:
            if nombre_nuevo.strip() == "":
                st.error("❌ El nombre no puede estar vacío.")
            else:
                nuevo_cliente = clientes.add_client(
                    nombre=nombre_nuevo,
                    telefono=telefono_nuevo,
                    ci=ci_nuevo,
                    chapa=chapa_nueva,
                    direccion=direccion_nueva,
                    usuario=st.session_state["usuario"]["username"]
                )
                st.success(f"✅ Cliente agregado: {nuevo_cliente['nombre']}")
                cliente_id = nuevo_cliente["id"]

# =========================
# 📦 Sección de productos
# =========================
if "items_venta" not in st.session_state:
    st.session_state["items_venta"] = []

productos_data = productos.list_products()
st.subheader("📦 Productos disponibles")

if productos_data:
    opciones = {
        f"{p['nombre']} (Stock: {p['cantidad']}, ${p['precio']:.2f})": p
        for p in productos_data
    }

    producto_nombre = st.selectbox(
        "Selecciona un producto",
        [""] + list(opciones.keys()),
        key="select_producto_ventas"
    )

    if producto_nombre:
        prod = opciones[producto_nombre]

        cantidad = st.number_input(
            "Cantidad",
            min_value=1,
            max_value=prod["cantidad"],
            value=1,
            key=f"cant_{prod['id']}"
        )

        precio = st.number_input(
            "Precio unitario",
            min_value=0.01,
            value=float(prod["precio"]),
            step=0.01,
            key=f"precio_{prod['id']}"
        )

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

# =========================
# 📝 Orden actual
# =========================
# =========================
# 📝 Orden actual
# =========================
if st.session_state["items_venta"]:
    st.subheader("📝 Orden actual")
    df = pd.DataFrame(st.session_state["items_venta"])
    df["subtotal"] = df["cantidad"] * df["precio_unitario"]
    df_resumen = df[["id_producto", "nombre", "cantidad", "precio_unitario", "subtotal"]]
    st.dataframe(df_resumen, use_container_width=True)

    total = df["subtotal"].astype(float).sum()
    st.subheader(f"💰 Total: ${total:,.2f}")

    col_a, col_b = st.columns([1, 1])
    with col_a:
        if st.button("🗑️ Vaciar orden", key="vaciar_orden"):
            st.session_state["items_venta"] = []
            st.success("🧹 Orden vaciada correctamente.")
            st.rerun()

    if cliente_id:
        pago_estado = st.radio("Estado del pago", ["Pagado", "Pendiente"])
        tipo_pago = st.selectbox(
            "Método de pago",
            ["Efectivo", "Transferencia", "Tarjeta", "Otro"],
            key="tipo_pago_venta"
        ) if pago_estado == "Pagado" else "Pendiente"

        with col_b:
            if st.button("💾 Registrar Venta", key="registrar_venta"):
                try:
                    # Determinar monto pagado
                    monto_pagado = float(total) if pago_estado == "Pagado" else 0.0

                    # Registrar venta
                    nueva_venta = ventas.register_sale(
                        cliente_id=cliente_id,
                        productos=st.session_state["items_venta"],
                        total=float(total),
                        pagado=monto_pagado,
                        usuario=st.session_state["usuario"]["username"],
                        tipo_pago=tipo_pago
                    )

                    # Si el pago está pendiente, crear deuda asociada a los productos
                    if pago_estado == "Pendiente":
                        from backend.deudas import add_debt
                        saldo_pendiente = float(total) - monto_pagado
                        add_debt(
                            cliente_id=cliente_id,
                            monto_total=saldo_pendiente,  # ✅ correcto
                            venta_id=nueva_venta["id"],
                            productos=st.session_state["items_venta"],
                            usuario=st.session_state["usuario"]["username"],
                            estado="pendiente"
                        )
                    st.success(f"Venta registrada ✅ ID {nueva_venta['id']} - Total ${nueva_venta['total']:,.2f}")

                    # Limpiar carrito
                    st.session_state["items_venta"] = []
                    st.rerun()

                except Exception :

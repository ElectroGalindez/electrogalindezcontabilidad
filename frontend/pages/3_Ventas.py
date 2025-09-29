if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()
import streamlit as st
import pandas as pd
from backend import productos, clientes, ventas

st.title("🛒 Registrar Venta")

# ---------------------------
# CLIENTE
# ---------------------------
st.subheader("👤 Cliente")

clientes_data = clientes.list_clients()
clientes_dict = {c["nombre"]: c["id"] for c in clientes_data}
cliente_id = None

if clientes_dict:
    cliente_nombre = st.selectbox("Selecciona un cliente", list(clientes_dict.keys()))
    cliente_id = clientes_dict[cliente_nombre]
else:
    st.warning("⚠️ No hay clientes registrados.")

# Botón para agregar cliente nuevo
if st.button("➕ Agregar nuevo cliente"):
    with st.form("form_nuevo_cliente", clear_on_submit=True):
        nombre_nuevo = st.text_input("Nombre del cliente")
        telefono_nuevo = st.text_input("Teléfono")
        submitted = st.form_submit_button("Guardar Cliente")

        if submitted:
            if nombre_nuevo.strip() == "":
                st.error("❌ El nombre no puede estar vacío.")
            else:
                nuevo_cliente = clientes.add_client(nombre_nuevo, telefono_nuevo)
                st.success(f"✅ Cliente agregado: {nuevo_cliente['nombre']}")
                cliente_id = nuevo_cliente["id"]

# ---------------------------
# PRODUCTOS
# ---------------------------
st.subheader("📦 Productos")

productos_data = productos.list_products()

# Inicializar lista de items en sesión
if "items_venta" not in st.session_state:
    st.session_state["items_venta"] = []

if productos_data:
    st.write("### ➕ Agregar productos a la venta")

    # Selector de producto
    opciones = {f"{p['nombre']} (Stock: {p['cantidad']}, ${p['precio']:.2f})": p for p in productos_data}
    seleccionado = st.selectbox("Selecciona un producto", [""] + list(opciones.keys()))

    if seleccionado:
        prod = opciones[seleccionado]

        # Validación de stock bajo
        if prod["cantidad"] == 0:
            st.error(f"❌ {prod['nombre']} no tiene stock disponible.")
        else:
            st.markdown(f"**Producto seleccionado:** {prod['nombre']} (Stock: {prod['cantidad']})")

            cantidad = st.number_input(
                "Cantidad",
                min_value=1,
                max_value=prod["cantidad"],
                step=1,
                key=f"cantidad_{prod['id']}"
            )

            precio = st.number_input(
                "Precio unitario",
                min_value=0.01,
                value=float(prod["precio"]),
                step=0.01,
                key=f"precio_{prod['id']}"
            )

            if st.button("➕ Añadir a la orden", key=f"add_{prod['id']}"):
                if cantidad > prod["cantidad"]:
                    st.error(f"⚠️ Stock insuficiente. Disponible: {prod['cantidad']}")
                elif prod["cantidad"] <= 2:
                    st.warning(f"⚠️ Stock muy bajo ({prod['cantidad']} disponibles). No se agregó a la orden.")
                else:
                    st.session_state["items_venta"].append({
                        "id_producto": prod["id"],
                        "nombre": prod["nombre"],
                        "cantidad": cantidad,
                        "precio_unitario": precio,
                        "subtotal": round(cantidad * precio, 2)
                    })
                    st.success(f"✅ {cantidad} x {prod['nombre']} añadido(s) a la orden")

# ---------------------------
# ORDEN
# ---------------------------
if st.session_state["items_venta"]:
    st.write("### 📝 Orden actual")

    df_orden = pd.DataFrame(st.session_state["items_venta"])
    df_orden["precio_unitario"] = df_orden["precio_unitario"].apply(lambda x: f"${x:,.2f}")
    df_orden["subtotal"] = df_orden["subtotal"].apply(lambda x: f"${x:,.2f}")

    st.dataframe(df_orden, use_container_width=True)

    total = sum(item["subtotal"] for item in st.session_state["items_venta"])
    st.subheader(f"💰 Total: ${total:,.2f}")

    # ---------------------------
    # PAGO
    # ---------------------------
    if cliente_id:
        pago_estado = st.radio("Estado del pago", ["Pagado", "Pendiente"])

        tipo_pago = None
        if pago_estado == "Pagado":
            tipo_pago = st.selectbox("Método de pago", ["Efectivo", "Transferencia", "Tarjeta", "Otro"])

        # ---------------------------
        # REGISTRAR VENTA
        # ---------------------------
        if st.button("💾 Registrar Venta"):
            pagado = total if pago_estado == "Pagado" else 0.0
            nueva = ventas.register_sale(cliente_id, st.session_state["items_venta"], pagado, tipo_pago)
            st.success(f"✅ Venta registrada: ID {nueva['id']} - Total ${nueva['total']:,.2f}")
            st.session_state["items_venta"] = []  # limpiar carrito
    else:
        st.info("👆 Selecciona o agrega un cliente para continuar.")

    # Botón para limpiar la orden
    if st.button("🗑️ Vaciar orden"):
        st.session_state["items_venta"] = []
        st.warning("Orden vaciada")

else:
    st.info("👆 Agrega productos para iniciar una orden.")

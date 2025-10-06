import streamlit as st
import pandas as pd
from datetime import datetime
from backend import productos, clientes, ventas

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
        key="select_cliente_existente"
    )
    if cliente_nombre:
        cliente_id = clientes_dict[cliente_nombre]

# Crear nuevo cliente
with st.expander("➕ Agregar nuevo cliente"):
    with st.form("form_nuevo_cliente", clear_on_submit=True):
        nombre_nuevo = st.text_input("Nombre del cliente", key="nuevo_nombre")
        telefono_nuevo = st.text_input("Teléfono", key="nuevo_telefono")
        ci_nuevo = st.text_input("C.I.", key="nuevo_ci")
        chapa_nueva = st.text_input("Chapa", key="nuevo_chapa")
        direccion_nueva = st.text_input("Dirección", key="nuevo_direccion")
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

# ---------------------------
# Inicializar items de venta
# ---------------------------
if "items_venta" not in st.session_state:
    st.session_state["items_venta"] = []

# ---------------------------
# Mostrar productos
# ---------------------------
st.subheader("📦 Productos")
productos_data = productos.list_products()

dtf_productos = pd.DataFrame(productos_data)

if productos_data:
    for p in productos_data:
        col1, col2, col3, col4 = st.columns([4, 2, 2, 2])
        with col1:
            st.text(p["nombre"])
        with col2:
            cantidad = st.number_input(
                f"Cantidad {p['id']}",
                min_value=0,
                max_value=p["cantidad"],
                value=0,
                step=1,
                key=f"cantidad_{p['id']}"
            )
        with col3:
            precio = st.number_input(
                f"Precio {p['id']}",
                min_value=0.01,
                value=float(p["precio"]),
                step=0.01,
                key=f"precio_{p['id']}"
            )
        with col4:
            if st.button(f"➕ Añadir {p['nombre']}", key=f"add_{p['id']}"):
                if cantidad > 0:
                    existente = next((i for i in st.session_state["items_venta"] if i["id_producto"] == p["id"]), None)
                    if existente:
                        total_cantidad = existente["cantidad"] + cantidad
                        if total_cantidad > p["cantidad"]:
                            st.error(f"⚠️ Stock insuficiente ({p['cantidad']} disponible)")
                        else:
                            existente["cantidad"] = total_cantidad
                            existente["precio_unitario"] = precio
                            st.success(f"✅ Cantidad actualizada: {total_cantidad} x {p['nombre']}")
                    else:
                        st.session_state["items_venta"].append({
                            "id_producto": p["id"],
                            "nombre": p["nombre"],
                            "cantidad": cantidad,
                            "precio_unitario": precio
                        })
                        st.success(f"✅ {cantidad} x {p['nombre']} añadido(s) a la orden")
# ---------------------------
# Orden acumulada
# ---------------------------
if st.session_state["items_venta"]:
    st.subheader("📝 Orden actual")
    df_orden = pd.DataFrame(st.session_state["items_venta"])
    df_orden["subtotal"] = df_orden["cantidad"] * df_orden["precio_unitario"]

    # Mostrar con formato
    df_display = df_orden.copy()
    df_display["precio_unitario"] = df_display["precio_unitario"].apply(lambda x: f"${x:,.2f}")
    df_display["subtotal"] = df_display["subtotal"].apply(lambda x: f"${x:,.2f}")
    st.dataframe(df_display, use_container_width=True)

    # Total
    total = df_orden["subtotal"].sum()
    st.subheader(f"💰 Total: ${total:,.2f}")

    # Registrar venta
    if cliente_id:
        pago_estado = st.radio("Estado del pago", ["Pagado", "Pendiente"], key="pago_estado")
        tipo_pago = st.selectbox(
            "Método de pago",
            ["Efectivo", "Transferencia", "Tarjeta", "Otro"],
            key="tipo_pago"
        ) if pago_estado == "Pagado" else None

        if st.button("💾 Registrar Venta", key="btn_registrar_venta"):
            pagado = total if pago_estado == "Pagado" else 0.0
            try:
                nueva = ventas.register_sale(
                    cliente_id=cliente_id,
                    items=st.session_state["items_venta"],
                    pagado=pagado,
                    tipo_pago=tipo_pago,
                    usuario=st.session_state["usuario"]["username"]
                )
                st.success(f"✅ Venta registrada: ID {nueva['id']} - Total ${nueva['total']:,.2f}")
                if pagado < nueva['total']:
                    st.warning(f"⚠️ Se generó una deuda pendiente de ${nueva['total'] - pagado:,.2f} para este cliente.")
                st.session_state["items_venta"] = []
            except Exception as e:
                st.error(f"❌ Error al registrar la venta: {str(e)}")

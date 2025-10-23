import streamlit as st
import pandas as pd
from io import BytesIO
import json
from backend import deudas, clientes, productos

# =============================
# CONFIGURACIÓN DE PÁGINA
# =============================
st.set_page_config(page_title="💳 Deudas por Producto", layout="wide")
st.title("💳 Gestión de Deudas por Producto")

# =============================
# VERIFICAR SESIÓN
# =============================
if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()

usuario_actual = st.session_state.usuario["username"]

# =============================
# CACHE DE DATOS
# =============================
@st.cache_data(ttl=10)
def cached_clients():
    return clientes.list_clients()

@st.cache_data(ttl=10)
def cached_products():
    return productos.list_products()

clientes_data = cached_clients()
productos_data = cached_products()
productos_map = {p["id"]: p["nombre"] for p in productos_data}

# =============================
# FILTRAR CLIENTES CON DEUDA
# =============================
clientes_con_deuda = [c for c in clientes_data if float(c.get("deuda_total", 0) or 0) > 0]

if not clientes_con_deuda:
    st.info("🎉 No hay clientes con deuda pendiente.")
    st.stop()

# =============================
# SELECCIÓN DE CLIENTE
# =============================
# Crear diccionario nombre → id
clientes_opciones = {c["nombre"]: c["id"] for c in clientes_con_deuda}

# Agregar opción inicial vacía
nombres_clientes = [""] + list(clientes_opciones.keys())

cliente_sel_nombre = st.selectbox(
    "👤 Seleccionar Cliente",
    nombres_clientes,
    index=0,
    key="cliente_sel",
    help="Busca un cliente por nombre"
)

# Si no ha seleccionado cliente, detener
if not cliente_sel_nombre:
    st.info("🔍 Selecciona un cliente para ver sus deudas.")
    st.stop()

# Obtener ID y datos del cliente seleccionado
cliente_id = clientes_opciones[cliente_sel_nombre]
cliente_obj = clientes.get_client(cliente_id)
deuda_total = float(cliente_obj.get("deuda_total", 0.0) or 0.0)

st.markdown(
    f"<h4>💰 Deuda total actual: <span style='color:#c0392b;'>${deuda_total:,.2f}</span></h4>",
    unsafe_allow_html=True
)
# =============================
# LISTAR DEUDAS POR CLIENTE
# =============================
deudas_historial = deudas.debts_by_client(cliente_id) or []

filas = []
for deuda in deudas_historial:
    for det in deuda.get("detalles", []):
        cantidad = float(det.get("cantidad") or 0)
        precio_unitario = float(det.get("precio_unitario") or 0)
        monto_total = cantidad * precio_unitario
        estado_det = det.get("estado", "pendiente").lower()
        if estado_det != "pendiente":
            continue  # solo pendientes
        filas.append({
            "Deuda ID": deuda["id"],
            "Producto ID": det.get("producto_id"),
            "Producto": productos_map.get(det.get("producto_id"), f"Producto {det.get('producto_id')}"),
            "Cantidad": round(cantidad, 2),
            "Precio Unitario": round(precio_unitario, 2),
            "Monto Total": round(monto_total, 2),
            "Estado": estado_det.capitalize(),
            "Fecha": str(deuda.get("fecha"))[:19]
        })

df_detalle = pd.DataFrame(filas)

# =============================
# TABLA DE DEUDAS POR CLIENTE
# =============================
st.subheader("📋 Deudas del Cliente Seleccionado")
if not df_detalle.empty:
    st.dataframe(
        df_detalle.sort_values(["Estado", "Deuda ID"], ascending=[True, False])
        .style.format({
            "Cantidad": "{:,.2f}",
            "Precio Unitario": "{:,.2f}",
            "Monto Total": "{:,.2f}"
        }),
        use_container_width=True
    )
else:
    st.info("✅ Este cliente no tiene productos pendientes de pago.")

# =============================
# REGISTRAR PAGO POR PRODUCTO
# =============================
pendientes = df_detalle[df_detalle["Estado"].str.lower() == "pendiente"]

if not pendientes.empty:
    st.divider()
    st.subheader("💵 Registrar Pago por Producto")

    producto_sel = st.selectbox(
        "Seleccionar producto a pagar",
        pendientes["Producto"].unique()
    )

    fila_producto = pendientes[pendientes["Producto"] == producto_sel].iloc[0]
    deuda_id = int(fila_producto["Deuda ID"])
    producto_id = int(fila_producto["Producto ID"])
    monto_max = float(fila_producto["Monto Total"])

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"💲 **Monto pendiente:** ${monto_max:,.2f}")
        st.write(f"🧾 **Deuda ID:** {deuda_id}")
        st.write(f"📦 **Producto:** {producto_sel}")

    monto_pago = st.number_input(
        "Monto a pagar",
        min_value=0.0,
        max_value=monto_max,
        step=0.01,
        value=monto_max
    )

    if st.button("💰 Registrar pago del producto"):
        try:
            resultado = deudas.pay_debt_producto(
                deuda_id,
                producto_id,
                monto_pago,
                usuario=usuario_actual
            )
            st.success(f"✅ Pago registrado para {producto_sel}: ${monto_pago:,.2f}")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error al registrar pago: {str(e)}")
else:
    st.info("No hay productos pendientes de pago.")

# =============================
# DESCARGA DE DEUDAS DEL CLIENTE
# =============================
if not df_detalle.empty:
    df_detalle["Fecha"] = pd.to_datetime(df_detalle["Fecha"], errors="coerce").dt.strftime("%Y-%m-%d")
    excel_buffer_cliente = BytesIO()
    with pd.ExcelWriter(excel_buffer_cliente, engine="xlsxwriter") as writer:
        df_detalle.to_excel(writer, index=False, sheet_name="DeudasCliente")
    excel_data_cliente = excel_buffer_cliente.getvalue()

    st.download_button(
        label="⬇️ Descargar deudas del cliente (Excel)",
        data=excel_data_cliente,
        file_name=f"deudas_cliente_{cliente_id}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="descargar_cliente_excel"
    )

# =============================
# TABLA GENERAL DE DEUDAS PENDIENTES
# =============================
st.subheader("📊 Todas las Deudas Pendientes (Clientes y Productos)")

detalles_totales = deudas.list_detalle_deudas() or []
filas_totales = []
for d in detalles_totales:
    cantidad = float(d.get("cantidad") or 0)
    precio_unitario = float(d.get("precio_unitario") or 0)
    monto_total = cantidad * precio_unitario
    estado_det = str(d.get("estado") or "pendiente").lower()
    if estado_det != "pendiente":
        continue  # solo pendientes
    cliente_id_d = d.get("cliente_id")
    cliente = clientes.get_client(cliente_id_d)
    nombre_cliente = cliente.get("nombre", "Desconocido") if cliente else "Sin datos"
    filas_totales.append({
        "Cliente": nombre_cliente,
        "Deuda ID": d.get("deuda_id"),
        "Producto ID": d.get("producto_id"),
        "Producto": productos_map.get(d.get("producto_id"), f"Producto {d.get('producto_id')}"),
        "Cantidad": round(cantidad, 2),
        "Precio Unitario": round(precio_unitario, 2),
        "Monto Total": round(monto_total, 2),
        "Estado": estado_det.capitalize(),
        "Fecha": str(d.get("fecha"))[:19]
    })

df_totales = pd.DataFrame(filas_totales)
if not df_totales.empty:
    st.dataframe(
        df_totales.sort_values(["Fecha", "Cliente"], ascending=[False, True])
        .style.format({
            "Cantidad": "{:,.2f}",
            "Precio Unitario": "${:,.2f}",
            "Monto Total": "${:,.2f}"
        }),
        use_container_width=True,
        height=500
    )
else:
    st.info("✅ No hay deudas pendientes registradas.")

# =============================
# DESCARGA TABLA GENERAL
# =============================
if not df_totales.empty:
    excel_buffer_general = BytesIO()
    with pd.ExcelWriter(excel_buffer_general, engine="xlsxwriter") as writer:
        df_totales.to_excel(writer, index=False, sheet_name="DeudasGenerales")
    excel_data_general = excel_buffer_general.getvalue()

    st.download_button(
        label="⬇️ Descargar tabla general de deudas (Excel)",
        data=excel_data_general,
        file_name=f"deudas_generales.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="descargar_general_excel"
    )

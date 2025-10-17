import streamlit as st
import pandas as pd
from backend.clientes import list_clients, get_client
from backend.deudas import debts_by_client, pay_debt_producto
from backend import productos

st.set_page_config(page_title="💳 Deudas por Producto", layout="wide")
st.title("💳 Gestión de Deudas por Producto")

# =============================
# Verificar sesión
# =============================
if "usuario" not in st.session_state or st.session_state.usuario is None:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    st.stop()

usuario_actual = st.session_state.usuario["username"]

# =============================
# Cache de datos
# =============================
@st.cache_data(ttl=10)
def cached_clients():
    return list_clients()

@st.cache_data(ttl=10)
def cached_products():
    return productos.list_products()

clientes_data = cached_clients()
productos_data = cached_products()
productos_map = {p["id"]: p["nombre"] for p in productos_data}

# =============================
# Filtrar clientes con deuda
# =============================
clientes_con_deuda = [c for c in clientes_data if float(c.get("deuda_total", 0)) > 0]

if not clientes_con_deuda:
    st.info("🎉 No hay clientes con deuda pendiente.")
    st.stop()

# =============================
# Selección de cliente
# =============================
cliente_opciones = [f"{c['id']} - {c['nombre']}" for c in clientes_con_deuda]
cliente_sel = st.selectbox("👤 Seleccionar Cliente", cliente_opciones, key="cliente_sel")
cliente_id = int(cliente_sel.split(" - ")[0])
cliente_obj = get_client(cliente_id)
deuda_total = float(cliente_obj.get("deuda_total", 0.0))

st.markdown(
    f"<h4>💰 Deuda total actual: <span style='color:#c0392b;'>${deuda_total:,.2f}</span></h4>",
    unsafe_allow_html=True
)

# =============================
# Construcción de tabla
# =============================
deudas_historial = debts_by_client(cliente_id) or []
if not deudas_historial:
    st.info("Este cliente no tiene deudas registradas.")
    st.stop()

filas = []
for deuda in deudas_historial:
    for det in deuda.get("detalles", []):
        prod_id = det.get("producto_id")
        nombre_producto = productos_map.get(prod_id, f"Producto {prod_id}")
        monto_total = float(det.get("cantidad", 0)) * float(det.get("precio_unitario", 0))
        filas.append({
            "Deuda ID": int(deuda["id"]),
            "Producto ID": int(prod_id),
            "Producto": nombre_producto,
            "Cantidad": round(float(det.get("cantidad", 0)), 2),
            "Precio Unitario": round(float(det.get("precio_unitario", 0)), 2),
            "Monto Total": round(monto_total, 2),
            "Estado": det.get("estado", "pendiente"),
            "Fecha": deuda.get("fecha")
        })

df_detalle = pd.DataFrame(filas)

# =============================
# Mostrar tabla de deudas
# =============================
st.subheader("📋 Deudas por Producto")
st.dataframe(
    df_detalle.sort_values(["Estado", "Deuda ID"], ascending=[True, False])
    .style.format({
        "Cantidad": "{:,.2f}",
        "Precio Unitario": "{:,.2f}",
        "Monto Total": "{:,.2f}"
    }),
    use_container_width=True
)

# =============================
# Registrar pago por producto
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
            resultado = pay_debt_producto(
                int(deuda_id),
                int(producto_id),
                float(monto_pago),
                usuario=usuario_actual
            )
            st.success(f"✅ Pago registrado para {producto_sel}: ${monto_pago:,.2f}")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error al registrar pago: {str(e)}")
else:
    st.info("No hay productos pendientes de pago.")


import json
import pandas as pd
import streamlit as st
from backend import ventas, clientes

st.subheader("📊 Tabla general de deudas por cliente y producto")

# Obtener todas las ventas registradas
ventas_data = ventas.list_sales()
deudas_tabla = []

for v in ventas_data:
    cliente_id = v.get("cliente_id")
    cliente = clientes.get_client(cliente_id)
    nombre_cliente = cliente.get("nombre", "Desconocido") if cliente else "Sin datos"

    productos_vendidos = v.get("productos_vendidos", [])

    # ✅ Cargar si es texto JSON
    if isinstance(productos_vendidos, str):
        try:
            productos_vendidos = json.loads(productos_vendidos)
        except json.JSONDecodeError:
            productos_vendidos = []

    # Si no hay productos, saltar
    if not productos_vendidos:
        continue

    # Buscar si hay algún producto con saldo o monto pendiente
    for p in productos_vendidos:
        nombre_prod = p.get("nombre") or p.get("producto") or "N/A"
        cantidad = float(p.get("cantidad") or p.get("cant") or 0)
        precio = float(p.get("precio_unitario") or p.get("precio") or 0)
        subtotal = cantidad * precio

        # 💡 Si existe saldo o el total de la venta es mayor a lo pagado, es deuda
        total_venta = float(v.get("total", 0) or 0)
        pagado = float(v.get("pagado", 0) or 0)
        saldo = float(v.get("saldo", 0) or (total_venta - pagado))

        if saldo > 0 or subtotal > 0:
            deudas_tabla.append({
                "Cliente": nombre_cliente,
                "Venta ID": v.get("id"),
                "Producto": nombre_prod,
                "Cantidad": cantidad,
                "Precio Unitario": precio,
                "Pagado": pagado,
                "Saldo Pendiente": saldo,
                "Fecha": str(v.get("fecha", ""))[:19]
            })

# Mostrar tabla si hay deudas
if deudas_tabla:
    df = pd.DataFrame(deudas_tabla)
    df = df[df["Saldo Pendiente"] > 0]  # Mostrar solo las deudas reales
    if not df.empty:
        st.dataframe(
            df.style.format({
                "Cantidad": "{:,.0f}",
                "Precio Unitario": "${:.2f}",
                "Subtotal": "${:.2f}",
                "Pagado": "${:.2f}",
                "Saldo Pendiente": "${:.2f}",
            }),
            use_container_width=True,
            height=500
        )
    else:
        st.info("✅ No hay deudas pendientes registradas.")
else:
    st.info("✅ No hay deudas pendientes registradas.")

# =============================
# 📥 Botón para descargar tabla de deudas del cliente actual en Excel
# =============================
from io import BytesIO
# =============================
# Corregir formato de fecha
# =============================
if "Fecha" in df_detalle.columns:
    df_detalle["Fecha"] = pd.to_datetime(df_detalle["Fecha"], errors="coerce")
    df_detalle["Fecha"] = df_detalle["Fecha"].dt.strftime("%Y-%m-%d")
    df_detalle["Hora"] = df_detalle["Hora"].fillna("").astype(str)


excel_buffer = BytesIO()
with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
    df_detalle.to_excel(writer, index=False, sheet_name="DeudasCliente")
excel_data = excel_buffer.getvalue()

st.download_button(
    label="⬇️ Descargar deudas del cliente (Excel)",
    data=excel_data,
    file_name=f"deudas_cliente_{cliente_obj['nombre'].replace(' ', '_')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    key="descargar_cliente_excel"
)
# =============================
# 📥 Botón para descargar tabla general en Excel
# =============================
from io import BytesIO

excel_buffer_general = BytesIO()
with pd.ExcelWriter(excel_buffer_general, engine="xlsxwriter") as writer:
    df.to_excel(writer, index=False, sheet_name="DeudasGenerales")
excel_data_general = excel_buffer_general.getvalue()

st.download_button(
    label="⬇️ Descargar tabla general de deudas (Excel)",
    data=excel_data_general,
    file_name="deudas_generales.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    key="descargar_general_excel"
)

import streamlit as st
import pandas as pd
import plotly.express as px
from backend.reportes import ventas_diarias, productos_mas_vendidos, deudas_clientes

st.title("📈 Reportes")

opcion = st.selectbox("Seleccionar Reporte", ["Ventas del Día", "Productos Más Vendidos", "Deudas Pendientes"])

if opcion == "Ventas del Día":
    ventas = ventas_diarias()
    if ventas:
        st.table(ventas)
    else:
        st.info("No hay ventas hoy")

elif opcion == "Productos Más Vendidos":
    data = productos_mas_vendidos()
    df = pd.DataFrame(data, columns=["Producto", "Cantidad"])
    fig = px.bar(df, x="Producto", y="Cantidad", title="Productos Más Vendidos")
    st.plotly_chart(fig)

elif opcion == "Deudas Pendientes":
    df = pd.DataFrame(deudas_clientes())
    if not df.empty:
        st.table(df)
    else:
        st.info("No hay deudas pendientes")

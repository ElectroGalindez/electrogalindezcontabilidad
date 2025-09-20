# frontend/📊 ElectroGalíndezContabilidad.py
import streamlit as st

st.set_page_config(
    page_title="ElectroGalíndez - Sistema Contable",
    page_icon="💰",
    layout="wide"
)

st.sidebar.success("Selecciona una opción en el menú")

st.title("📊 ElectroGalíndez - Sistema de Contabilidad")
st.markdown("""
Bienvenido al sistema contable de **ElectroGalíndez**.  
Usa el menú lateral para acceder a:
- 📦 Inventario  
- 🛒 Ventas  
- 💳 Pagos  
- 📈 Reportes
""")

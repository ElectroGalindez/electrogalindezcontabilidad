import streamlit as st
import pandas as pd
import json
from pathlib import Path

# Cargar datos
DATA_PATH = Path("data")

def cargar_json(nombre):
    with open(DATA_PATH / nombre, "r") as f:
        return json.load(f)

st.title("📊 Sistema de Contabilidad del Almacén")

menu = st.sidebar.radio("Menú", ["Inventario", "Ventas", "Deudas", "Reportes"])

if menu == "Inventario":
    productos = cargar_json("productos.json")
    st.subheader("📦 Inventario")
    st.table(pd.DataFrame(productos))

elif menu == "Ventas":
    st.subheader("🛒 Registrar venta")
    st.info("Aquí iría el formulario para registrar ventas...")

elif menu == "Deudas":
    st.subheader("💰 Pagos de clientes")
    st.info("Aquí se muestran y actualizan las deudas...")

elif menu == "Reportes":
    st.subheader("📈 Reportes")
    st.info("Gráficas de ventas y deudas...")

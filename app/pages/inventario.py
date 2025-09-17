import streamlit as st
import pandas as pd
import json
from pathlib import Path

DATA_PATH = Path("../data")  # ../ porque pages/ está dentro de app/

def cargar_json(nombre):
    with open(DATA_PATH / nombre, "r") as f:
        return json.load(f)

st.set_page_config(page_title="Inventario")
st.title("📦 Inventario")

productos = cargar_json("productos.json")
st.table(pd.DataFrame(productos))


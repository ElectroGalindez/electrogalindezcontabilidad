import datetime
from backend.ventas import list_sales
from collections import Counter
import json
from pathlib import Path
import pandas as pd


def ventas_diarias(fecha=None):
    if not fecha:
        fecha = str(datetime.date.today())
    return [v for v in list_sales() if v["fecha"] == fecha]

def ventas_mensuales(mes, anio):
    result = []
    for v in list_sales():
        v_fecha = datetime.datetime.strptime(v["fecha"], "%Y-%m-%d")
        if v_fecha.month == mes and v_fecha.year == anio:
            result.append(v)
    return result

def productos_mas_vendidos():
    counter = Counter()
    for v in list_sales():
        for p in v["productos_vendidos"]:
            counter[p["nombre"]] += p["cantidad"]
    return counter.most_common()

def deudas_clientes():
    with open("data/deudas.json", "r") as f:
        deudas = json.load(f)
    
    if not deudas:
        return pd.DataFrame(columns=["id", "cliente_id", "monto", "estado", "fecha"])
    
    return pd.DataFrame(deudas) 
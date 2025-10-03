# backend/ventas.py
from datetime import datetime
import json
import os

VENTAS_FILE = "./data/ventas.json"

def load_sales():
    if os.path.exists(VENTAS_FILE):
        with open(VENTAS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_sales(ventas):
    with open(VENTAS_FILE, "w", encoding="utf-8") as f:
        json.dump(ventas, f, ensure_ascii=False, indent=4)

def generar_id():
    import uuid
    return str(uuid.uuid4())[:8]

def register_sale(cliente_id, productos_vendidos, pagado=0.0, tipo_pago=None, fecha=None):
    if fecha is None:
        fecha = datetime.now()
    total = sum(p["subtotal"] for p in productos_vendidos)
    venta = {
        "id": generar_id(),
        "cliente_id": cliente_id,
        "productos_vendidos": productos_vendidos,
        "total": total,
        "pagado": pagado,
        "tipo_pago": tipo_pago,
        "fecha": fecha.isoformat()  # Guardamos fecha con hora
    }
    ventas = load_sales()
    ventas.append(venta)
    save_sales(ventas)
    return venta

def list_sales():
    return load_sales()

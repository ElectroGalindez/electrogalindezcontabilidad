import json
import os
import datetime
from backend.productos import load_products, save_products
from backend.clientes import update_client_debt
from backend.exceptions import NotFoundError, InsufficientStockError

DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/ventas.json")
DEUDAS_PATH = os.path.join(os.path.dirname(__file__), "../data/deudas.json")

def load_sales():
    with open(DATA_PATH, "r") as f:
        return json.load(f)

def save_sales(sales):
    with open(DATA_PATH, "w") as f:
        json.dump(sales, f, indent=4, ensure_ascii=False)

def load_deudas():
    with open(DEUDAS_PATH, "r") as f:
        return json.load(f)

def save_deudas(deudas):
    with open(DEUDAS_PATH, "w") as f:
        json.dump(deudas, f, indent=4, ensure_ascii=False)

def register_sale(cliente_id, items, pagado):
    products = load_products()
    total = 0
    productos_vendidos = []

    for item in items:
        prod = next((p for p in products if p["id"] == item["id"]), None)
        if not prod:
            raise NotFoundError(f"Producto {item['id']} no encontrado")
        if prod["cantidad"] < item["cantidad"]:
            raise InsufficientStockError(f"Stock insuficiente para {prod['nombre']}")
        prod["cantidad"] -= item["cantidad"]
        subtotal = prod["precio"] * item["cantidad"]
        total += subtotal
        productos_vendidos.append({
            "id": prod["id"],
            "nombre": prod["nombre"],
            "cantidad": item["cantidad"],
            "precio": prod["precio"]
        })

    save_products(products)

    sale = {
        "id": str(len(load_sales()) + 1),
        "fecha": str(datetime.date.today()),
        "cliente_id": cliente_id,
        "productos_vendidos": productos_vendidos,
        "total": total,
        "pagado": pagado
    }

    sales = load_sales()
    sales.append(sale)
    save_sales(sales)

    if pagado < total:
        deuda = {
            "id": str(len(load_deudas()) + 1),
            "cliente_id": cliente_id,
            "monto": total - pagado,
            "estado": "pendiente",
            "fecha": str(datetime.date.today())
        }
        deudas = load_deudas()
        deudas.append(deuda)
        save_deudas(deudas)
        update_client_debt(cliente_id, total - pagado)

    return sale

def list_sales():
    return load_sales()

def get_sale(sale_id):
    sales = load_sales()
    for s in sales:
        if s["id"] == sale_id:
            return s
    raise NotFoundError("Venta no encontrada")

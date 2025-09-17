import json
import os
from backend.exceptions import NotFoundError, ValidationError, InsufficientStockError

DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/productos.json")

def load_products():
    with open(DATA_PATH, "r") as f:
        return json.load(f)

def save_products(products):
    with open(DATA_PATH, "w") as f:
        json.dump(products, f, indent=4, ensure_ascii=False)

def add_product(product):
    products = load_products()
    if any(p['id'] == product['id'] for p in products):
        raise ValidationError("El producto ya existe")
    products.append(product)
    save_products(products)

def edit_product(product_id, updated_product):
    products = load_products()
    for i, p in enumerate(products):
        if p['id'] == product_id:
            products[i].update(updated_product)
            save_products(products)
            return
    raise NotFoundError("Producto no encontrado")

def delete_product(product_id):
    products = load_products()
    products = [p for p in products if p['id'] != product_id]
    save_products(products)

def get_product(product_id):
    products = load_products()
    for p in products:
        if p['id'] == product_id:
            return p
    raise NotFoundError("Producto no encontrado")

def list_products():
    return load_products()

import json
import os
from backend.exceptions import NotFoundError, ValidationError

DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/clientes.json")

def load_clients():
    with open(DATA_PATH, "r") as f:
        return json.load(f)

def save_clients(clients):
    with open(DATA_PATH, "w") as f:
        json.dump(clients, f, indent=4, ensure_ascii=False)

def add_client(client):
    clients = load_clients()
    if any(c['id'] == client['id'] for c in clients):
        raise ValidationError("El cliente ya existe")
    clients.append(client)
    save_clients(clients)

def update_client_debt(client_id, amount):
    clients = load_clients()
    for c in clients:
        if c['id'] == client_id:
            c['deuda_total'] += amount
            save_clients(clients)
            return
    raise NotFoundError("Cliente no encontrado")

def get_client(client_id):
    clients = load_clients()
    for c in clients:
        if c['id'] == client_id:
            return c
    raise NotFoundError("Cliente no encontrado")

def list_clients():
    return load_clients()

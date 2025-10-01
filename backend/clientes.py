# ---------------------------
# ELIMINAR CLIENTE
# ---------------------------
def delete_client(cliente_id: str, usuario=None) -> bool:
    clients = list_clients()
    cliente_eliminado = next((c for c in clients if c["id"] == cliente_id), None)
    clients = [c for c in clients if c["id"] != cliente_id]
    write_json_atomic(FILENAME, clients)
    # Registrar log de eliminación de cliente
    try:
        from .logs import registrar_log
        registrar_log(usuario or "sistema", "eliminar_cliente", {
            "cliente_id": cliente_id,
            "cliente": cliente_eliminado
        })
    except Exception:
        pass
    return True
"""
Módulo para manejo de clientes.
Funciones públicas:
- list_clients()
- get_client(cliente_id)
- add_client(nombre, telefono)
- edit_client(cliente_id, cambios)
- update_debt(cliente_id, monto)  # suma (o resta) deuda_total
"""

from typing import List, Dict, Any, Optional
from .utils import read_json, write_json_atomic, generate_id, validate_client

FILENAME = "clientes.json"


# ---------------------------
# LISTAR Y OBTENER CLIENTES
# ---------------------------
def list_clients() -> List[Dict[str, Any]]:
    return read_json(FILENAME)


def get_client(cliente_id: str) -> Optional[Dict[str, Any]]:
    clients = list_clients()
    for c in clients:
        if c["id"] == cliente_id:
            return c
    return None


# ---------------------------
# AGREGAR CLIENTE
# ---------------------------
def add_client(nombre: str, telefono: str = "", usuario=None) -> Dict[str, Any]:
    clients = list_clients()
    cliente_data = {
        "id": generate_id("C", clients),
        "nombre": nombre,
        "telefono": telefono,
        "deuda_total": 0.0
    }
    if not validate_client(cliente_data):
        raise ValueError("Estructura de cliente inválida")
    clients.append(cliente_data)
    write_json_atomic(FILENAME, clients)
    # Registrar log de creación de cliente
    try:
        from .logs import registrar_log
        registrar_log(usuario or "sistema", "crear_cliente", {
            "cliente_id": cliente_data["id"],
            "nombre": nombre,
            "telefono": telefono
        })
    except Exception:
        pass
    return cliente_data


# ---------------------------
# EDITAR CLIENTE
# ---------------------------
def edit_client(cliente_id: str, cambios: Dict[str, Any], usuario=None) -> Dict[str, Any]:
    """
    Permite actualizar datos del cliente.
    Ejemplo: edit_client("C1", {"nombre": "Nuevo Nombre", "telefono": "123"})
    """
    clients = list_clients()
    for c in clients:
        if c["id"] == cliente_id:
            c.update(cambios)
            if not validate_client(c):
                raise ValueError("Datos de cliente inválidos tras la edición")
            write_json_atomic(FILENAME, clients)
            # Registrar log de edición de cliente
            try:
                from .logs import registrar_log
                registrar_log(usuario or "sistema", "editar_cliente", {
                    "cliente_id": cliente_id,
                    "cambios": cambios
                })
            except Exception:
                pass
            return c
    raise KeyError(f"Cliente {cliente_id} no encontrado")


# ---------------------------
# ACTUALIZAR DEUDA
# ---------------------------
def update_debt(cliente_id: str, monto: float) -> Dict[str, Any]:
    """
    Suma (monto positivo) o resta (monto negativo) la deuda_total del cliente.
    Devuelve el cliente actualizado.
    """
    clients = list_clients()
    for c in clients:
        if c["id"] == cliente_id:
            c["deuda_total"] = float(c.get("deuda_total", 0.0)) + float(monto)
            # Evitar deuda negativa
            if c["deuda_total"] < 0:
                c["deuda_total"] = 0.0
            write_json_atomic(FILENAME, clients)
            return c
    raise KeyError(f"Cliente {cliente_id} no encontrado")

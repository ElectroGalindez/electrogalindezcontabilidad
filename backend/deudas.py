# backend/deudas.py
from typing import List, Dict, Any, Optional
from .utils import read_json, write_json_atomic, generate_id, iso_today

FILENAME = "../data/deudas.json"  # Ajusta según tu estructura

def list_debts() -> List[Dict[str, Any]]:
    """Devuelve todas las deudas."""
    return read_json(FILENAME)

def debts_by_client(cliente_id: str) -> List[Dict[str, Any]]:
    """Devuelve las deudas pendientes de un cliente."""
    return [d for d in list_debts() if d["cliente_id"] == cliente_id and d["estado"] != "pagada"]

def add_debt(cliente_id: str, productos: List[Dict[str, Any]], usuario: Optional[str] = None) -> Dict[str, Any]:
    """
    Crea una nueva deuda por productos.
    Cada producto debe tener: id_producto, nombre, cantidad, precio_unitario, subtotal, saldo
    """
    deudas = list_debts()
    total = sum(p["saldo"] for p in productos)
    nueva_deuda = {
        "id": generate_id("D", deudas),
        "cliente_id": cliente_id,
        "productos": productos,
        "monto_total": total,
        "estado": "pendiente",
        "fecha": iso_today(),
        "usuario": usuario or "sistema"
    }
    deudas.append(nueva_deuda)
    write_json_atomic(FILENAME, deudas)
    return nueva_deuda

def pay_debt(deuda_id: str, monto: float) -> Dict[str, Any]:
    """Registra un pago sobre una deuda específica y actualiza los saldos por producto."""
    deudas = list_debts()
    deuda = next((d for d in deudas if d["id"] == deuda_id), None)
    if deuda is None:
        raise KeyError(f"Deuda {deuda_id} no encontrada")

    if deuda["estado"] == "pagada":
        return deuda  # ya pagada

    restante = monto
    for prod in deuda["productos"]:
        if restante <= 0:
            break
        saldo_actual = prod["saldo"]
        abono = min(restante, saldo_actual)
        prod["saldo"] -= abono
        restante -= abono

    deuda["monto_total"] = sum(p["saldo"] for p in deuda["productos"])
    deuda["estado"] = "pagada" if deuda["monto_total"] == 0 else "pendiente"

    write_json_atomic(FILENAME, deudas)
    return deuda

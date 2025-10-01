# backend/deudas.py
"""
Módulo para manejar deudas individuales.
Funciones públicas:
- list_debts()
- add_debt(cliente_id, monto, fecha=None, estado='pendiente')
- pay_debt(debt_id, monto_pago)  # registra pago parcial o total sobre una deuda
- get_debt(debt_id)
- debts_by_client(cliente_id)
"""
from typing import Optional
from typing import List, Dict, Any
from .utils import read_json, write_json_atomic, generate_id, iso_today, validate_debt
from .clientes import update_debt, get_client

FILENAME = "deudas.json"

def list_debts() -> List[Dict[str, Any]]:
    return read_json(FILENAME)

def get_debt(debt_id: str) -> Optional[Dict[str, Any]]:
    for d in list_debts():
        if d["id"] == debt_id:
            return d
    return None

def add_debt(cliente_id: str, monto: float, fecha: Optional[str] = None, estado: str = "pendiente", usuario: Optional[str] = None) -> Dict[str, Any]:
    deudas = list_debts()
    if fecha is None:
        fecha = iso_today()
    debt_obj = {
        "id": generate_id("D", deudas),
        "cliente_id": cliente_id,
        "monto": float(monto),
        "estado": estado,
        "fecha": fecha
    }
    if not validate_debt(debt_obj):
        raise ValueError("Estructura de deuda inválida")
    deudas.append(debt_obj)
    write_json_atomic(FILENAME, deudas)
    # actualizar deuda_total en clientes
    update_debt(cliente_id, monto)
    # Registrar log de creación de deuda
    try:
        from .logs import registrar_log
        registrar_log(usuario or "sistema", "crear_deuda", {
            "deuda_id": debt_obj["id"],
            "cliente_id": cliente_id,
            "monto": monto,
            "estado": estado
        })
    except Exception:
        pass
    return debt_obj

def pay_debt(debt_id: str, monto_pago: float, usuario: Optional[str] = None) -> Dict[str, Any]:
    """
    Aplica monto de pago a una deuda específica.
    - Si monto_pago >= monto => deuda marcada 'pagada' y monto ajustado a 0.
    - Si pago parcial => se resta el monto y queda pendiente.
    También actualiza deuda_total del cliente.
    """
    deudas = list_debts()
    found = False
    for d in deudas:
        if d["id"] == debt_id:
            found = True
            saldo = float(d["monto"])
            pago = float(monto_pago)
            if pago >= saldo:
                # pago total
                d["monto"] = 0.0
                d["estado"] = "pagada"
                ajuste = -saldo
            else:
                d["monto"] = round(saldo - pago, 2)
                d["estado"] = "pendiente"
                ajuste = -pago
            write_json_atomic(FILENAME, deudas)
            # actualizar cliente
            update_debt(d["cliente_id"], ajuste)
            # Registrar log de pago de deuda
            try:
                from .logs import registrar_log
                registrar_log(usuario or "sistema", "pago_deuda", {
                    "deuda_id": d["id"],
                    "cliente_id": d["cliente_id"],
                    "monto_pago": monto_pago,
                    "estado_final": d["estado"]
                })
            except Exception:
                pass
            return d
    if not found:
        raise KeyError(f"Deuda {debt_id} no encontrada")

def debts_by_client(cliente_id: str) -> List[Dict[str, Any]]:
    return [d for d in list_debts() if d["cliente_id"] == cliente_id]

# Eliminar deuda
def delete_debt(debt_id: str, usuario: Optional[str] = None) -> bool:
    deudas = list_debts()
    deuda_eliminada = next((d for d in deudas if d["id"] == debt_id), None)
    deudas = [d for d in deudas if d["id"] != debt_id]
    write_json_atomic(FILENAME, deudas)
    # Registrar log de eliminación de deuda
    try:
        from .logs import registrar_log
        registrar_log(usuario or "sistema", "eliminar_deuda", {
            "deuda_id": debt_id,
            "deuda": deuda_eliminada
        })
    except Exception:
        pass
    return True

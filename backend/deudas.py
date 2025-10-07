# backend/deudas.py
"""
Módulo para manejar deudas individuales en PostgreSQL.
Funciones públicas:
- list_debts()
- add_debt(cliente_id, monto, venta_id=None, fecha=None, estado='pendiente')
- pay_debt(debt_id, monto_pago)
- get_debt(debt_id)
- debts_by_client(cliente_id)
- delete_debt(debt_id)
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import text
from .db import engine
import json
from .clientes import update_debt, get_client

# ---------------------------
# Listar todas las deudas
# ---------------------------
def list_debts() -> List[Dict[str, Any]]:
    query = text("SELECT * FROM deudas")
    with engine.connect() as conn:
        result = conn.execute(query)
        return [dict(row._mapping) for row in result]

# ---------------------------
# Obtener deuda específica
# ---------------------------
def get_debt(debt_id: int) -> Optional[Dict[str, Any]]:
    query = text("SELECT * FROM deudas WHERE id = :id")
    with engine.connect() as conn:
        result = conn.execute(query, {"id": debt_id}).mappings().first()
        return dict(result) if result else None

# ---------------------------
# Crear deuda nueva
# ---------------------------


def add_debt(cliente_id: int, monto: float, venta_id: int = None, fecha: datetime = None,
             estado: str = "pendiente", usuario: str = None, productos: list = None):
    """
    Crea un registro de deuda en la base de datos incluyendo productos.
    """
    if fecha is None:
        fecha = datetime.now()

    productos_json = json.dumps(productos or [])

    query = text("""
        INSERT INTO deudas (cliente_id, venta_id, monto_total, estado, fecha, descripcion, productos)
        VALUES (:cliente_id, :venta_id, :monto, :estado, :fecha, :descripcion, :productos)
        RETURNING id
    """)

    with engine.begin() as conn:
        result = conn.execute(query, {
            "cliente_id": cliente_id,
            "venta_id": venta_id,
            "monto": monto,
            "estado": estado,
            "fecha": fecha,
            "descripcion": f"Deuda generada por venta {venta_id or 'N/A'}",
            "productos": productos_json
        })
        deuda_id = result.scalar()

    return deuda_id


# ---------------------------
# Pagar deuda
# ---------------------------
def pay_debt(debt_id: int, monto_pago: float, usuario: Optional[str] = None) -> Dict[str, Any]:
    deuda = get_debt(debt_id)
    if not deuda:
        raise KeyError(f"Deuda {debt_id} no encontrada")

    saldo = float(deuda["monto_total"])
    pago = float(monto_pago)

    if pago >= saldo:
        nuevo_saldo = 0.0
        nuevo_estado = "pagada"
        ajuste = -saldo
    else:
        nuevo_saldo = round(saldo - pago, 2)
        nuevo_estado = "pendiente"
        ajuste = -pago

    query = text("""
        UPDATE deudas
        SET monto_total = :nuevo_saldo, estado = :nuevo_estado
        WHERE id = :id
        RETURNING *
    """)
    with engine.begin() as conn:
        result = conn.execute(query, {
            "nuevo_saldo": nuevo_saldo,
            "nuevo_estado": nuevo_estado,
            "id": debt_id
        }).mappings().first()
    
    # Actualizar deuda_total del cliente
    update_debt(deuda["cliente_id"], ajuste)

    # Registrar log
    try:
        from .logs import registrar_log
        registrar_log(usuario or "sistema", "pago_deuda", {
            "deuda_id": debt_id,
            "cliente_id": deuda["cliente_id"],
            "monto_pago": monto_pago,
            "estado_final": nuevo_estado
        })
    except Exception:
        pass

    return dict(result)

# ---------------------------
# Deudas por cliente
# ---------------------------

def debts_by_client(cliente_id):
    query = text("""
        SELECT id, cliente_id, venta_id, monto_total, estado, fecha, descripcion, productos
        FROM deudas
        WHERE cliente_id = :cliente_id
        ORDER BY fecha DESC
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"cliente_id": cliente_id})
        # result.mappings() devuelve diccionarios
        return [dict(row) for row in result.mappings()]

# ---------------------------
# Eliminar deuda
# ---------------------------
def delete_debt(debt_id: int, usuario: Optional[str] = None) -> bool:
    deuda = get_debt(debt_id)
    if not deuda:
        return False

    query = text("DELETE FROM deudas WHERE id = :id")
    with engine.begin() as conn:
        conn.execute(query, {"id": debt_id})

    # Ajustar deuda_total del cliente
    update_debt(deuda["cliente_id"], -float(deuda["monto_total"]))

    # Registrar log
    try:
        from .logs import registrar_log
        registrar_log(usuario or "sistema", "eliminar_deuda", {
            "deuda_id": debt_id,
            "deuda": deuda
        })
    except Exception:
        pass

    return True

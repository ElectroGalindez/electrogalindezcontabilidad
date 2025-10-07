"""
Módulo para manejar deudas y sus detalles (por producto) en PostgreSQL.

Funciones públicas:
- list_debts()
- get_debt(debt_id)
- add_debt(cliente_id, monto_total, venta_id=None, productos=None, usuario=None)
- pay_debt(debt_id, monto_pago, usuario=None)
- debts_by_client(cliente_id)
- delete_debt(debt_id, usuario=None)
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import text
from .db import engine
from .clientes import update_debt
import json

# ======================================================
# 📜 Listar todas las deudas
# ======================================================
def list_debts() -> List[Dict[str, Any]]:
    query = text("SELECT * FROM deudas ORDER BY fecha DESC")
    with engine.connect() as conn:
        result = conn.execute(query)
        return [dict(row._mapping) for row in result]


# ======================================================
# 🔍 Obtener deuda específica
# ======================================================
def get_debt(debt_id: int) -> Optional[Dict[str, Any]]:
    query = text("""
        SELECT d.*, json_agg(dd.*) AS detalles
        FROM deudas d
        LEFT JOIN deudas_detalle dd ON d.id = dd.deuda_id
        WHERE d.id = :id
        GROUP BY d.id
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"id": debt_id}).mappings().first()
        return dict(result) if result else None


# ======================================================
# ➕ Crear deuda nueva (con detalles por producto)
# ======================================================
def add_debt(
    cliente_id: int,
    venta_id: int = None,
    fecha: datetime = None,
    estado: str = "pendiente",
    usuario: str = None,
    productos: list = None,
    monto_total: float = 0.0
):
    """
    Crea un registro de deuda y sus detalles por producto en la base de datos.
    """
    if fecha is None:
        fecha = datetime.now()

    productos_json = json.dumps(productos or [])

    # Insertar deuda principal
    query_deuda = text("""
        INSERT INTO deudas (cliente_id, venta_id, monto, estado, fecha, descripcion, productos)
        VALUES (:cliente_id, :venta_id, :monto_total, :estado, :fecha, :descripcion, :productos)
        RETURNING id
    """)
    with engine.begin() as conn:
        result = conn.execute(query_deuda, {
            "cliente_id": cliente_id,
            "venta_id": venta_id,
            "monto": monto_total,
            "estado": estado,
            "fecha": fecha,
            "descripcion": f"Deuda generada por venta {venta_id or 'N/A'}",
            "productos": productos_json
        })
        deuda_id = result.scalar()

        # Insertar detalles por producto
        if productos:
            for item in productos:
                conn.execute(text("""
                    INSERT INTO deudas_detalle (deuda_id, producto_id, cantidad, precio_unitario, estado)
                    VALUES (:deuda_id, :producto_id, :cantidad, :precio_unitario, :estado)
                """), {
                    "deuda_id": deuda_id,
                    "producto_id": item.get("id_producto"),
                    "cantidad": item.get("cantidad", 0),
                    "precio_unitario": item.get("precio_unitario", 0),
                    "estado": "pendiente"
                })

    return deuda_id

# ======================================================
# 💵 Registrar pago de deuda
# ======================================================
def pay_debt(debt_id: int, monto_pago: float, usuario: Optional[str] = None) -> Dict[str, Any]:
    deuda = get_debt(debt_id)
    if not deuda:
        raise KeyError(f"Deuda {debt_id} no encontrada")

    saldo = float(deuda["monto_total"])
    pago = float(monto_pago)

    if pago <= 0:
        raise ValueError("El monto de pago debe ser mayor que 0")

    if pago > saldo:
        pago = saldo  # Evita pagar más de lo debido

    nuevo_saldo = round(saldo - pago, 2)
    nuevo_estado = "pagada" if nuevo_saldo == 0 else "pendiente"

    with engine.begin() as conn:
        # Actualizar deuda principal
        update_query = text("""
            UPDATE deudas
            SET monto_total = :nuevo_saldo, estado = :nuevo_estado
            WHERE id = :id
            RETURNING *
        """)
        result = conn.execute(update_query, {
            "nuevo_saldo": nuevo_saldo,
            "nuevo_estado": nuevo_estado,
            "id": debt_id
        }).mappings().first()

        # Actualizar detalles proporcionalmente (FIFO)
        if deuda.get("detalles"):
            restante = pago
            for det in sorted(deuda["detalles"], key=lambda d: d["id"]):
                if restante <= 0:
                    break

                monto_det = float(det["monto"])
                if monto_det <= restante:
                    # Se paga completo el detalle
                    conn.execute(text("""
                        UPDATE deudas_detalle SET estado = 'pagado' WHERE id = :id
                    """), {"id": det["id"]})
                    restante -= monto_det
                else:
                    # Pago parcial → se reduce proporcionalmente
                    nuevo_monto = monto_det - restante
                    nuevo_precio = nuevo_monto / det["cantidad"]
                    conn.execute(text("""
                        UPDATE deudas_detalle
                        SET precio_unitario = :nuevo_precio
                        WHERE id = :id
                    """), {"nuevo_precio": nuevo_precio, "id": det["id"]})
                    restante = 0

    # Actualizar deuda_total del cliente
    update_debt(deuda["cliente_id"], -pago)

    # Log del pago
    try:
        from .logs import registrar_log
        registrar_log(usuario or "sistema", "pago_deuda", {
            "deuda_id": debt_id,
            "cliente_id": deuda["cliente_id"],
            "monto_pago": pago,
            "saldo_restante": nuevo_saldo,
            "estado_final": nuevo_estado
        })
    except Exception:
        pass

    return dict(result)


# ======================================================
# 📋 Listar deudas por cliente
# ======================================================
def debts_by_client(cliente_id: int):
    query = text("""
        SELECT d.id, d.fecha, d.estado, d.monto_total, d.descripcion, 
               json_agg(dd.*) AS detalles
        FROM deudas d
        LEFT JOIN deudas_detalle dd ON d.id = dd.deuda_id
        WHERE d.cliente_id = :cliente_id
        GROUP BY d.id
        ORDER BY d.fecha DESC
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"cliente_id": cliente_id})
        return [dict(row._mapping) for row in result]


# ======================================================
# 🗑️ Eliminar deuda
# ======================================================
def delete_debt(debt_id: int, usuario: Optional[str] = None) -> bool:
    deuda = get_debt(debt_id)
    if not deuda:
        return False

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM deudas_detalle WHERE deuda_id = :id"), {"id": debt_id})
        conn.execute(text("DELETE FROM deudas WHERE id = :id"), {"id": debt_id})

    update_debt(deuda["cliente_id"], -float(deuda["monto_total"]))

    try:
        from .logs import registrar_log
        registrar_log(usuario or "sistema", "eliminar_deuda", {
            "deuda_id": debt_id,
            "cliente_id": deuda["cliente_id"],
            "monto_total": deuda["monto_total"]
        })
    except Exception:
        pass

    return True

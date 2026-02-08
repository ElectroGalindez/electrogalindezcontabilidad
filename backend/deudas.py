"""
Módulo para manejar deudas y pagos por producto en PostgreSQL.

Funciones públicas:
- list_debts()
- get_debt(deuda_id)
- add_debt(cliente_id, venta_id=None, productos=None, usuario=None)
- pay_debt_producto(deuda_id, producto_id, monto_pago, usuario=None)
- debts_by_client(cliente_id)
- delete_debt(deuda_id, usuario=None)
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from .db import get_connection
from .clientes import update_debt
import json

# ======================================================
# 📜 Listar todas las deudas
# ======================================================
def list_debts() -> List[Dict[str, Any]]:
    query = "SELECT * FROM deudas ORDER BY fecha DESC"
    with get_connection() as conn:
        result = conn.execute(query)
        return [dict(row) for row in result.fetchall()]

# ======================================================
# 🔍 Obtener deuda con detalles
# ======================================================
def get_debt(deuda_id: int) -> Optional[Dict[str, Any]]:
    query = "SELECT * FROM deudas WHERE id = ?"
    with get_connection() as conn:
        result = conn.execute(query, (deuda_id,)).fetchone()
        if not result:
            return None
        detalles = conn.execute(
            "SELECT * FROM deudas_detalle WHERE deuda_id = ?",
            (deuda_id,),
        ).fetchall()
        r = dict(result)
        r["detalles"] = [dict(row) for row in detalles]
        return r

# ======================================================
# ➕ Crear deuda con detalles por producto
# ======================================================
def add_debt(
    cliente_id: int,
    venta_id: int = None,
    productos: list = None,  # lista de dicts: {id_producto, cantidad, precio_unitario}
    monto_total: float = 0.0,
    estado: str = "pendiente",
    usuario: str = None
) -> int:
    """
    Crea una deuda general y registros por producto en deudas_detalle.
    """
    fecha = datetime.now().isoformat()
    productos_json = json.dumps(productos or [])

    with get_connection() as conn:
        # Insertar deuda principal
        query = """
            INSERT INTO deudas (cliente_id, venta_id, monto_total, estado, fecha, descripcion, productos)
            VALUES (:cliente_id, :venta_id, :monto_total, :estado, :fecha, :descripcion, :productos)
        """
        cursor = conn.execute(query, {
            "cliente_id": cliente_id,
            "venta_id": venta_id,
            "monto_total": monto_total,
            "estado": estado,
            "fecha": fecha,
            "descripcion": f"Deuda generada por venta {venta_id or 'N/A'}",
            "productos": productos_json
        })
        deuda_id = cursor.lastrowid

        # Insertar detalles por producto
        if productos:
            for p in productos:
                conn.execute("""
                    INSERT INTO deudas_detalle (deuda_id, producto_id, cantidad, precio_unitario, estado)
                    VALUES (:deuda_id, :producto_id, :cantidad, :precio_unitario, 'pendiente')
                """, {
                    "deuda_id": deuda_id,
                    "producto_id": p["id_producto"],
                    "cantidad": p["cantidad"],
                    "precio_unitario": p["precio_unitario"]
                })

    # Actualizar deuda total del cliente
    update_debt(cliente_id, monto_total)
    return deuda_id

# ======================================================
# 💵 Registrar pago de deuda por producto
# ======================================================
def pay_debt_producto(deuda_id: int, producto_id: int, monto_pago: float, usuario: Optional[str] = None) -> Dict[str, Any]:
    """
    Aplica un pago solo sobre un detalle de deuda (producto) específico.
    """
    deuda = get_debt(deuda_id)
    if not deuda:
        raise KeyError(f"Deuda {deuda_id} no encontrada")

    detalle = next((d for d in deuda.get("detalles", []) if d["producto_id"] == producto_id), None)
    if not detalle:
        raise KeyError(f"Producto {producto_id} no encontrado en la deuda {deuda_id}")

    monto_detalle = float(detalle["cantidad"]) * float(detalle["precio_unitario"])
    if monto_pago <= 0 or monto_pago > monto_detalle:
        raise ValueError(f"Monto de pago inválido. Debe ser entre 0 y {monto_detalle}")

    nuevo_saldo_det = monto_detalle - monto_pago
    nuevo_estado_det = "pagado" if nuevo_saldo_det == 0 else "pendiente"

    with get_connection() as conn:
        if nuevo_estado_det == "pagado":
            conn.execute(
                "UPDATE deudas_detalle SET estado='pagado' WHERE id=:id",
                {"id": detalle["id"]},
            )
        else:
            # Ajusta el precio unitario proporcionalmente si es pago parcial
            nuevo_precio_unit = nuevo_saldo_det / float(detalle["cantidad"])
            conn.execute(
                "UPDATE deudas_detalle SET precio_unitario=:nuevo_precio WHERE id=:id",
                {"nuevo_precio": nuevo_precio_unit, "id": detalle["id"]},
            )

        # Actualizar deuda principal
        nuevo_monto_total = round(float(deuda["monto_total"]) - monto_pago, 2)
        nuevo_estado = "pagada" if nuevo_monto_total == 0 else "pendiente"
        conn.execute("""
            UPDATE deudas
            SET monto_total=:nuevo_monto_total, estado=:nuevo_estado
            WHERE id=:id
        """, {"nuevo_monto_total": nuevo_monto_total, "nuevo_estado": nuevo_estado, "id": deuda_id})
        result = conn.execute("SELECT * FROM deudas WHERE id = ?", (deuda_id,)).fetchone()

    # Actualizar deuda total del cliente
    update_debt(deuda["cliente_id"], -monto_pago)

    # Registrar log
    try:
        from .logs import registrar_log
        registrar_log(usuario or "sistema", "pago_deuda_producto", {
            "deuda_id": deuda_id,
            "cliente_id": deuda["cliente_id"],
            "producto_id": producto_id,
            "monto_pago": monto_pago,
            "saldo_restante": nuevo_saldo_det,
            "estado_final": nuevo_estado_det
        })
    except Exception:
        pass

    return dict(result) if result else {}

# ======================================================
# 📋 Listar deudas por cliente
# ======================================================
def debts_by_client(cliente_id: int):
    query = """
        SELECT id, fecha, estado, monto_total, descripcion
        FROM deudas
        WHERE cliente_id = ?
        ORDER BY fecha DESC
    """
    with get_connection() as conn:
        result = conn.execute(query, (cliente_id,)).fetchall()
        deudas = []
        for deuda in result:
            detalles = conn.execute(
                "SELECT * FROM deudas_detalle WHERE deuda_id = ?",
                (deuda["id"],),
            ).fetchall()
            deuda_dict = dict(deuda)
            deuda_dict["detalles"] = [dict(row) for row in detalles]
            deudas.append(deuda_dict)
        return deudas

# ======================================================
# 🗑️ Eliminar deuda
# ======================================================
def delete_debt(deuda_id: int, usuario: Optional[str] = None) -> bool:
    deuda = get_debt(deuda_id)
    if not deuda:
        return False

    with get_connection() as conn:
        conn.execute("DELETE FROM deudas_detalle WHERE deuda_id = ?", (deuda_id,))
        conn.execute("DELETE FROM deudas WHERE id = ?", (deuda_id,))

    update_debt(deuda["cliente_id"], -float(deuda["monto_total"]))

    try:
        from .logs import registrar_log
        registrar_log(usuario or "sistema", "eliminar_deuda", {
            "deuda_id": deuda_id,
            "cliente_id": deuda["cliente_id"],
            "monto_total": deuda["monto_total"]
        })
    except Exception:
        pass

    return True

# ======================================================
# 📊 Listar todos los detalles de deudas (deudas_detalle)
# ======================================================
def list_detalle_deudas():
    """
    Devuelve una lista de todos los detalles de deuda, 
    incluyendo datos del cliente, monto, estado y fecha.
    """
    query = """
        SELECT 
            dd.id AS detalle_id,
            dd.deuda_id,
            dd.producto_id,
            dd.cantidad,
            dd.precio_unitario,
            dd.estado,
            d.cliente_id,
            d.fecha,
            d.monto_total,
            d.estado AS estado_deuda
        FROM deudas_detalle dd
        JOIN deudas d ON d.id = dd.deuda_id
        ORDER BY d.fecha DESC
    """
    with get_connection() as conn:
        result = conn.execute(query)
        return [dict(row) for row in result.fetchall()]


# ======================================================
# 📋 Listar clientes con deudas pendiente
# ======================================================
def list_clientes_con_deuda():
    """
    Devuelve una lista de clientes que tienen deudas pendientes.
    """
    query = """
        SELECT DISTINCT c.id, c.nombre, c.deuda_total
        FROM clientes c
        JOIN deudas d ON c.id = d.cliente_id
        WHERE d.estado = 'pendiente' AND c.deuda_total > 0
        ORDER BY c.nombre
    """
    with get_connection() as conn:
        result = conn.execute(query)
        return [dict(row) for row in result.fetchall()]
    

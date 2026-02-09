"""Debt management helpers."""

from __future__ import annotations

from datetime import datetime
import json
from typing import Any, Dict, List, Optional

from .clientes import update_debt
from .db import get_connection
from .logs import registrar_log


def list_debts() -> List[Dict[str, Any]]:
    """Listar todas las deudas registradas."""
    query = "SELECT * FROM deudas ORDER BY fecha DESC"
    with get_connection() as conn:
        result = conn.execute(query)
        return [dict(row) for row in result.fetchall()]


def get_debt(deuda_id: int) -> Optional[Dict[str, Any]]:
    """Obtener una deuda con sus detalles asociados."""
    query = "SELECT * FROM deudas WHERE id = ?"
    with get_connection() as conn:
        result = conn.execute(query, (deuda_id,)).fetchone()
        if not result:
            return None
        detalles = conn.execute(
            "SELECT * FROM deudas_detalle WHERE deuda_id = ?",
            (deuda_id,),
        ).fetchall()
        r_dict = dict(result)
        r_dict["detalles"] = [dict(row) for row in detalles]
        return r_dict


def add_debt(
    cliente_id: int,
    venta_id: int | None = None,
    productos: list | None = None,
    monto_total: float = 0.0,
    estado: str = "pendiente",
    usuario: str | None = None,
) -> int:
    """Crear una deuda con detalles por producto."""
    fecha = datetime.now().isoformat()
    productos_json = json.dumps(productos or [])

    with get_connection() as conn:
        query = """
            INSERT INTO deudas (cliente_id, venta_id, monto_total, estado, fecha, descripcion, productos)
            VALUES (:cliente_id, :venta_id, :monto_total, :estado, :fecha, :descripcion, :productos)
        """
        cursor = conn.execute(
            query,
            {
                "cliente_id": cliente_id,
                "venta_id": venta_id,
                "monto_total": monto_total,
                "estado": estado,
                "fecha": fecha,
                "descripcion": f"Deuda generada por venta {venta_id or 'N/A'}",
                "productos": productos_json,
            },
        )
        deuda_id = cursor.lastrowid

        if productos:
            for producto in productos:
                conn.execute(
                    """
                    INSERT INTO deudas_detalle (deuda_id, producto_id, cantidad, precio_unitario, estado)
                    VALUES (:deuda_id, :producto_id, :cantidad, :precio_unitario, 'pendiente')
                """,
                    {
                        "deuda_id": deuda_id,
                        "producto_id": producto["id_producto"],
                        "cantidad": producto["cantidad"],
                        "precio_unitario": producto["precio_unitario"],
                    },
                )

    update_debt(cliente_id, monto_total)
    registrar_log(usuario or "sistema", "crear_deuda", {"deuda_id": deuda_id, "cliente_id": cliente_id})
    return deuda_id


def pay_debt_producto(
    deuda_id: int,
    producto_id: int,
    monto_pago: float,
    usuario: Optional[str] = None,
) -> Dict[str, Any]:
    """Aplicar un pago sobre un producto específico de una deuda."""
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
            nuevo_precio_unit = nuevo_saldo_det / float(detalle["cantidad"])
            conn.execute(
                "UPDATE deudas_detalle SET precio_unitario=:nuevo_precio WHERE id=:id",
                {"nuevo_precio": nuevo_precio_unit, "id": detalle["id"]},
            )

        nuevo_monto_total = round(float(deuda["monto_total"]) - monto_pago, 2)
        nuevo_estado = "pagada" if nuevo_monto_total == 0 else "pendiente"
        conn.execute(
            """
            UPDATE deudas
            SET monto_total=:nuevo_monto_total, estado=:nuevo_estado
            WHERE id=:id
        """,
            {"nuevo_monto_total": nuevo_monto_total, "nuevo_estado": nuevo_estado, "id": deuda_id},
        )
        result = conn.execute("SELECT * FROM deudas WHERE id = ?", (deuda_id,)).fetchone()

    update_debt(deuda["cliente_id"], -monto_pago)

    registrar_log(
        usuario or "sistema",
        "pago_deuda_producto",
        {
            "deuda_id": deuda_id,
            "cliente_id": deuda["cliente_id"],
            "producto_id": producto_id,
            "monto_pago": monto_pago,
            "saldo_restante": nuevo_saldo_det,
            "estado_final": nuevo_estado_det,
        },
    )

    return dict(result) if result else {}


def debts_by_client(cliente_id: int) -> List[Dict[str, Any]]:
    """Listar deudas de un cliente con sus detalles."""
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


def delete_debt(deuda_id: int, usuario: Optional[str] = None) -> bool:
    """Eliminar una deuda y sus detalles asociados."""
    deuda = get_debt(deuda_id)
    if not deuda:
        return False

    with get_connection() as conn:
        conn.execute("DELETE FROM deudas_detalle WHERE deuda_id = ?", (deuda_id,))
        conn.execute("DELETE FROM deudas WHERE id = ?", (deuda_id,))

    update_debt(deuda["cliente_id"], -float(deuda["monto_total"]))

    registrar_log(
        usuario or "sistema",
        "eliminar_deuda",
        {"deuda_id": deuda_id, "cliente_id": deuda["cliente_id"], "monto_total": deuda["monto_total"]},
    )

    return True


def list_detalle_deudas() -> List[Dict[str, Any]]:
    """Listar todos los detalles de deuda con información asociada."""
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


def list_clientes_con_deuda() -> List[Dict[str, Any]]:
    """Listar clientes con deudas pendientes."""
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

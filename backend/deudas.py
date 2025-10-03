# backend/deudas.py
from sqlalchemy import text
from backend.db import engine

# =============================
# Funciones de gestión de deudas
# =============================

def list_debts():
    """Devuelve todas las deudas."""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id, cliente_id, monto_total, estado, fecha, usuario FROM deudas ORDER BY fecha")
        )
        deudas = [dict(row._mapping) for row in result]
    return deudas

def debts_by_client(cliente_id):
    """Devuelve las deudas pendientes de un cliente."""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id, cliente_id, monto_total, estado, fecha, usuario FROM deudas "
                 "WHERE cliente_id=:cid AND estado!='pagada' ORDER BY fecha"),
            {"cid": cliente_id}
        )
        return [dict(row._mapping) for row in result]

def add_debt(cliente_id, productos, usuario=None):
    """
    Crea una nueva deuda asociada a productos.
    Cada producto debe tener: id_producto, nombre, cantidad, precio_unitario, subtotal, saldo
    """
    if not productos:
        raise ValueError("Debe proporcionar al menos un producto para generar deuda")

    # Generar ID tipo D001, D002...
    deudas_existentes = list_debts()
    next_id = f"D{len(deudas_existentes)+1:03d}"

    monto_total = sum(float(p.get("saldo", p.get("subtotal", 0))) for p in productos)

    # Guardar deuda
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO deudas (id, cliente_id, monto_total, estado, fecha, usuario) "
                 "VALUES (:id, :cliente_id, :monto_total, :estado, :fecha, :usuario)"),
            {
                "id": next_id,
                "cliente_id": cliente_id,
                "monto_total": monto_total,
                "estado": "pendiente",
                "fecha": text("CURRENT_DATE"),  # fecha actual del servidor
                "usuario": usuario or "sistema"
            }
        )

        # Insertar detalle de productos vendidos en deuda_detalle
        for p in productos:
            conn.execute(
                text("INSERT INTO deuda_detalle (deuda_id, id_producto, nombre, cantidad, precio_unitario, subtotal, saldo) "
                     "VALUES (:deuda_id, :id_producto, :nombre, :cantidad, :precio_unitario, :subtotal, :saldo)"),
                {
                    "deuda_id": next_id,
                    "id_producto": p.get("id_producto", ""),
                    "nombre": p["nombre"],
                    "cantidad": p["cantidad"],
                    "precio_unitario": p["precio_unitario"],
                    "subtotal": p["subtotal"],
                    "saldo": p.get("saldo", p["subtotal"])
                }
            )

    return get_debt(next_id)

def get_debt(deuda_id):
    """Obtiene la deuda por ID incluyendo detalle de productos."""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id, cliente_id, monto_total, estado, fecha, usuario FROM deudas WHERE id=:id"),
            {"id": deuda_id}
        )
        deuda = result.fetchone()
        if not deuda:
            return None
        deuda_dict = dict(deuda._mapping)

        detalle_result = conn.execute(
            text("SELECT id_producto, nombre, cantidad, precio_unitario, subtotal, saldo "
                 "FROM deuda_detalle WHERE deuda_id=:deuda_id"),
            {"deuda_id": deuda_id}
        )
        deuda_dict["productos"] = [dict(r._mapping) for r in detalle_result]

    return deuda_dict

def pay_debt(deuda_id, monto):
    """
    Registra un pago sobre una deuda específica y actualiza los saldos por producto.
    """
    deuda = get_debt(deuda_id)
    if not deuda:
        raise KeyError(f"Deuda {deuda_id} no encontrada")

    if deuda["estado"] == "pagada":
        return deuda  # ya pagada

    restante = monto

    with engine.begin() as conn:
        for prod in deuda["productos"]:
            if restante <= 0:
                break
            saldo_actual = float(prod["saldo"])
            abono = min(restante, saldo_actual)
            nuevo_saldo = saldo_actual - abono
            conn.execute(
                text("UPDATE deuda_detalle SET saldo=:saldo WHERE deuda_id=:deuda_id AND id_producto=:id_producto"),
                {"saldo": nuevo_saldo, "deuda_id": deuda_id, "id_producto": prod.get("id_producto", "")}
            )
            restante -= abono

        # Actualizar monto_total y estado de la deuda
        result = conn.execute(
            text("SELECT SUM(saldo) as total_restante FROM deuda_detalle WHERE deuda_id=:deuda_id"),
            {"deuda_id": deuda_id}
        )
        total_restante = result.fetchone()["total_restante"] or 0.0
        estado = "pagada" if total_restante <= 0 else "pendiente"

        conn.execute(
            text("UPDATE deudas SET monto_total=:total, estado=:estado WHERE id=:deuda_id"),
            {"total": total_restante, "estado": estado, "deuda_id": deuda_id}
        )

    return get_debt(deuda_id)

from typing import Optional
from typing import List, Dict, Any

# Eliminar venta
def delete_sale(sale_id: str, usuario: Optional[str] = None) -> bool:
    ventas = list_sales()
    venta_eliminada = next((v for v in ventas if v["id"] == sale_id), None)
    ventas = [v for v in ventas if v["id"] != sale_id]
    write_json_atomic(FILENAME, ventas)
    # Registrar log de eliminación de venta
    try:
        from .logs import registrar_log
        registrar_log(usuario or "sistema", "eliminar_venta", {
            "venta_id": sale_id,
            "venta": venta_eliminada
        })
    except Exception:
        pass
    return True
# backend/ventas.py
"""
Módulo para registrar ventas y su efecto en inventario y deudas.
Funciones públicas:
- list_sales()
- get_sale(sale_id)
- register_sale(cliente_id, items, pagado)
  items = [ {"id_producto": "...", "cantidad": N, "precio_unitario": X }, ... ]
"""

from typing import List, Dict, Any, Optional
from .utils import read_json, write_json_atomic, generate_id, iso_today, validate_sale
from .productos import get_product, adjust_stock, list_products
from .deudas import add_debt
from .clientes import list_clients, get_client

FILENAME = "ventas.json"

def list_sales() -> List[Dict[str, Any]]:
    return read_json(FILENAME)

def get_sale(sale_id: str) -> Optional[Dict[str, Any]]:
    for s in list_sales():
        if s["id"] == sale_id:
            return s
    return None

def _calculate_total(items: List[Dict[str, Any]]) -> float:
    total = 0.0
    for it in items:
        total += float(it["cantidad"]) * float(it["precio_unitario"])
    return round(total, 2)

def register_sale(cliente_id: str, items: List[Dict[str, Any]], pagado: float, tipo_pago: Optional[str] = None, usuario: Optional[str] = None) -> Dict[str, Any]:
    """
    Registra una venta:
    - Verifica disponibilidad de stock
    - Descuenta stock
    - Guarda en ventas.json
    - Si hay deuda, la registra
    """
    # Validar cliente
    if get_client(cliente_id) is None:
        raise KeyError(f"Cliente {cliente_id} no existe")

    # Validar productos y stock
    for it in items:
        prod = get_product(it["id_producto"])
        if prod is None:
            raise KeyError(f"Producto {it['id_producto']} no existe")
        if prod.get("cantidad", 0) < it["cantidad"]:
            raise ValueError(f"Stock insuficiente para {it['id_producto']} (disponible {prod.get('cantidad', 0)})")

    # Calcular total
    total = _calculate_total(items)

    # Descontar stock
    for it in items:
        adjust_stock(it["id_producto"], -int(it["cantidad"]))

    # Crear registro de venta
    ventas = list_sales()
    new_sale = {
        "id": generate_id("V", ventas),
        "fecha": iso_today(),
        "cliente_id": cliente_id,
        "productos_vendidos": items,
        "total": total,
        "pagado": float(pagado),
        "tipo_pago": tipo_pago,
    }

    if not validate_sale(new_sale):
        raise ValueError("Estructura de venta inválida")

    ventas.append(new_sale)
    write_json_atomic(FILENAME, ventas)

    # Si no pagó todo, registrar deuda
    if pagado < total:
        diferencia = round(total - pagado, 2)
        add_debt(cliente_id, diferencia, usuario=usuario)

    # Registrar log de venta
    try:
        from .logs import registrar_log
        registrar_log(usuario or "sistema", "registrar_venta", {
            "venta_id": new_sale["id"],
            "cliente_id": cliente_id,
            "total": total,
            "pagado": pagado,
            "tipo_pago": tipo_pago,
            "productos": items
        })
    except Exception:
        pass
    return new_sale

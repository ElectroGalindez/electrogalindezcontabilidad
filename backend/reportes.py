"""Report generation helpers."""

import datetime
import json
from collections import Counter
from typing import Any, List

import pandas as pd

from core.paths import resolve_repo_path
from .logs import registrar_log
from .ventas import list_sales


def ventas_diarias(fecha: str | None = None, actor: str | None = None) -> List[Any]:
    """Generar el reporte de ventas diarias para una fecha dada."""
    if not fecha:
        fecha = str(datetime.date.today())
    resultado = []
    for venta in list_sales():
        venta_fecha = venta.get("fecha")
        if isinstance(venta_fecha, datetime.datetime):
            venta_fecha = venta_fecha.date().isoformat()
        if venta_fecha == fecha:
            resultado.append(venta)
    registrar_log(
        usuario=actor or "sistema",
        accion="reporte_ventas_diarias",
        detalles={"fecha": fecha, "total_registros": len(resultado)},
    )
    return resultado


def ventas_mensuales(mes: int, anio: int, actor: str | None = None) -> List[Any]:
    """Generar el reporte de ventas mensuales."""
    result = []
    for venta in list_sales():
        v_fecha = venta.get("fecha")
        if isinstance(v_fecha, str):
            v_fecha = datetime.datetime.strptime(v_fecha, "%Y-%m-%d")
        if isinstance(v_fecha, datetime.datetime) and v_fecha.month == mes and v_fecha.year == anio:
            result.append(venta)
    registrar_log(
        usuario=actor or "sistema",
        accion="reporte_ventas_mensuales",
        detalles={"mes": mes, "anio": anio, "total_registros": len(result)},
    )
    return result


def productos_mas_vendidos(actor: str | None = None) -> List[Any]:
    """Calcular el listado de productos más vendidos."""
    counter = Counter()
    for v in list_sales():
        for p in v["productos_vendidos"]:
            counter[p["nombre"]] += p["cantidad"]
    resultado = counter.most_common()
    registrar_log(
        usuario=actor or "sistema",
        accion="reporte_productos_mas_vendidos",
        detalles={"total_productos": len(resultado)},
    )
    return resultado


def deudas_clientes(actor: str | None = None) -> pd.DataFrame:
    """Generar un DataFrame con las deudas almacenadas en JSON."""
    deudas_path = resolve_repo_path("data", "deudas.json")
    if deudas_path.exists():
        with deudas_path.open("r", encoding="utf-8") as f:
            deudas = json.load(f)
    else:
        deudas = []

    if not deudas:
        df = pd.DataFrame(columns=["id", "cliente_id", "monto", "estado", "fecha"])
    else:
        df = pd.DataFrame(deudas)

    registrar_log(
        usuario=actor or "sistema",
        accion="reporte_deudas_clientes",
        detalles={"total_registros": len(df)},
    )
    return df

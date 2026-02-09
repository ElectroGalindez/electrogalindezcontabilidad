"""Helpers to filter audit logs by entity and record."""

from typing import Any, Dict, List

from .logs import listar_logs


def historial_por_registro(entidad: str, id_registro: Any) -> List[Dict[str, Any]]:
    """Devolver logs relacionados con una entidad e ID específico."""
    logs = listar_logs()
    resultado = []
    for log in logs:
        detalles = log.get("detalles", {})
        if detalles.get(f"{entidad}_id") == id_registro:
            resultado.append(log)
        elif detalles.get(entidad) and detalles[entidad].get("id") == id_registro:
            resultado.append(log)
    return resultado

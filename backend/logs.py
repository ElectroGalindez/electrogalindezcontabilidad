# backend/logs.py
from backend.db import engine
from sqlalchemy import text
from datetime import datetime

ACCIONES_IMPORTANTES = {
    "crear_usuario",
    "editar_usuario",
    "cambiar_password",
    "desactivar_usuario",
    "eliminar_usuario",
    "crear_producto",
    "editar_producto",
    "eliminar_producto",
    "registrar_venta",
    "pago_deuda",
    "enviar_alerta",
    "restaurar_backup"
}

# ---------------------------
# Registrar log
# ---------------------------
def registrar_log(usuario, accion, detalles=None, nivel="INFO"):
    if accion not in ACCIONES_IMPORTANTES and nivel != "CRITICAL":
        return None

    query = text("""
        INSERT INTO logs (usuario, accion, detalles, fecha, nivel)
        VALUES (:usuario, :accion, :detalles, :fecha, :nivel)
    """)
    with engine.begin() as conn:
        conn.execute(query, {
            "usuario": usuario,
            "accion": accion,
            "detalles": str(detalles or {}),
            "fecha": datetime.now(),
            "nivel": nivel
        })
    return True

# ---------------------------
# Registrar errores críticos
# ---------------------------
def registrar_error(usuario, mensaje, detalles=None):
    return registrar_log(
        usuario,
        accion="ERROR",
        detalles={"mensaje": mensaje, **(detalles or {})},
        nivel="CRITICAL"
    )

# ---------------------------
# Consultas
# ---------------------------
def listar_logs():
    query = text("SELECT * FROM logs ORDER BY fecha DESC")
    with engine.connect() as conn:
        result = conn.execute(query)
        return [dict(r) for r in result]

def obtener_logs_usuario(username):
    query = text("SELECT * FROM logs WHERE usuario=:usuario ORDER BY fecha DESC")
    with engine.connect() as conn:
        result = conn.execute(query, {"usuario": username})
        return [dict(r) for r in result]

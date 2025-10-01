import json
from pathlib import Path
from datetime import datetime

# ---------------------------
# Configuración de archivos
# ---------------------------
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
LOGS_FILE = DATA_DIR / "logs.json"
DATA_DIR.mkdir(exist_ok=True)

# ---------------------------
# Acciones importantes
# ---------------------------
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
# Cargar y guardar logs
# ---------------------------
def cargar_logs(mes=None):
    """Cargar logs desde archivo JSON. Si mes (YYYY-MM) está indicado, carga logs de ese mes."""
    path = DATA_DIR / f"logs_{mes}.json" if mes else LOGS_FILE
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_logs(logs, mes=None):
    """Guardar logs en JSON. Si mes (YYYY-MM) está indicado, guarda logs de ese mes."""
    path = DATA_DIR / f"logs_{mes}.json" if mes else LOGS_FILE
    with open(path, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=4, ensure_ascii=False)

# ---------------------------
# Registrar log principal
# ---------------------------
def registrar_log(usuario, accion, detalles=None, nivel="INFO"):
    """
    Registra un evento importante.
    Solo guarda acciones definidas en ACCIONES_IMPORTANTES o errores críticos.
    """
    if accion not in ACCIONES_IMPORTANTES and nivel != "CRITICAL":
        return None  # ignorar acciones triviales

    logs = cargar_logs()
    nuevo = {
        "usuario": usuario,
        "accion": accion,
        "detalles": detalles or {},
        "fecha": datetime.now().isoformat(),
        "nivel": nivel
    }
    logs.append(nuevo)
    guardar_logs(logs)
    return nuevo

# ---------------------------
# Registrar errores críticos
# ---------------------------
def registrar_error(usuario, mensaje, detalles=None):
    """
    Registra un error crítico en los logs (nivel CRITICAL).
    """
    return registrar_log(
        usuario,
        accion="ERROR",
        detalles={"mensaje": mensaje, **(detalles or {})},
        nivel="CRITICAL"
    )

# ---------------------------
# Funciones de consulta
# ---------------------------
def listar_logs(mes=None):
    """Devuelve todos los logs (opcionalmente de un mes)."""
    return cargar_logs(mes)

def obtener_logs_usuario(username, mes=None):
    """Devuelve logs filtrados por usuario."""
    logs = cargar_logs(mes)
    return [log for log in logs if log["usuario"] == username]

# ---------------------------
# Export
# ---------------------------
__all__ = [
    "registrar_log",
    "registrar_error",
    "listar_logs",
    "obtener_logs_usuario"
]

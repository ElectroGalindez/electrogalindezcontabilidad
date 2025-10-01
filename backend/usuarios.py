import json
import bcrypt
from pathlib import Path
from datetime import datetime, timedelta
from .logs import registrar_log
from typing import Optional

USERS_FILE = Path(__file__).resolve().parents[1] / "data" / "users.json"

# =============================
# Funciones de usuarios
# =============================
def cargar_usuarios():
    if not USERS_FILE.exists():
        return []
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_usuarios(usuarios):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=4, ensure_ascii=False)

def crear_usuario(username, password, rol="empleado", actor=None):
    usuarios = cargar_usuarios()
    if any(u["username"] == username for u in usuarios):
        raise ValueError("El usuario ya existe.")
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    nuevo = {
        "username": username,
        "password": hashed,
        "rol": rol,
        "activo": True,
        "created_at": datetime.now().isoformat(),
        "requiere_cambio_password": True,
        "intentos_fallidos": 0,
        "bloqueado_hasta": None
    }
    usuarios.append(nuevo)
    guardar_usuarios(usuarios)
    registrar_log(
        usuario=actor or username,
        accion="crear_usuario",
        detalles={"username": username, "rol": rol}
    )
    return nuevo

def autenticar_usuario(username, password, max_intentos=5, bloqueo_min=15):
    usuarios = cargar_usuarios()
    for u in usuarios:
        if u["username"] == username and u["activo"]:
            # Verificar si está bloqueado
            if u.get("bloqueado_hasta"):
                try:
                    bloqueado_hasta = datetime.fromisoformat(u["bloqueado_hasta"]) if u["bloqueado_hasta"] else None
                except Exception:
                    bloqueado_hasta = None
                if bloqueado_hasta and bloqueado_hasta > datetime.now():
                    return {"bloqueado": True, "bloqueado_hasta": bloqueado_hasta.isoformat()}
                else:
                    u["bloqueado_hasta"] = None
                    u["intentos_fallidos"] = 0
                    guardar_usuarios(usuarios)
            # Verificar contraseña
            if bcrypt.checkpw(password.encode(), u["password"].encode()):
                u["intentos_fallidos"] = 0
                guardar_usuarios(usuarios)
                return u
            else:
                u["intentos_fallidos"] = u.get("intentos_fallidos", 0) + 1
                if u["intentos_fallidos"] >= max_intentos:
                    u["bloqueado_hasta"] = (datetime.now() + timedelta(minutes=bloqueo_min)).isoformat()
                    registrar_log(
                        usuario=username,
                        accion="bloqueo_usuario",
                        detalles={"motivo": "demasiados intentos fallidos", "bloqueado_hasta": u["bloqueado_hasta"]}
                    )
                guardar_usuarios(usuarios)
                return None
    return None

def cambiar_password(username, new_password, actor=None):
    usuarios = cargar_usuarios()
    for u in usuarios:
        if u["username"] == username:
            u["password"] = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            u["requiere_cambio_password"] = False
            guardar_usuarios(usuarios)
            registrar_log(
                usuario=actor or username,
                accion="cambiar_password",
                detalles={"username": username}
            )
            return True
    return False

def cambiar_rol(username, nuevo_rol, actor=None):
    usuarios = cargar_usuarios()
    for u in usuarios:
        if u["username"] == username:
            old_rol = u["rol"]
            u["rol"] = nuevo_rol
            guardar_usuarios(usuarios)
            registrar_log(
                usuario=actor or username,
                accion="cambiar_rol",
                detalles={"username": username, "rol_anterior": old_rol, "rol_nuevo": nuevo_rol}
            )
            return True
    return False

def desactivar_usuario(username, actor=None):
    usuarios = cargar_usuarios()
    for u in usuarios:
        if u["username"] == username:
            u["activo"] = False
            guardar_usuarios(usuarios)
            registrar_log(
                usuario=actor or username,
                accion="desactivar_usuario",
                detalles={"username": username}
            )
            return True
    return False

def listar_usuarios():
    return cargar_usuarios()

def requiere_cambio_password(username):
    usuarios = cargar_usuarios()
    for u in usuarios:
        if u["username"] == username:
            return u.get("requiere_cambio_password", False)
    return False

def validar_usuario(username: str, password: str) -> Optional[dict]:
    """
    Valida si el usuario y contraseña existen.
    Retorna el diccionario del usuario si es válido, o None si no.
    """
    usuarios = listar_usuarios()  # tu función existente que carga todos los usuarios
    for u in usuarios:
        if u["username"] == username and u["password"] == password and u.get("activo", True):
            return u
    return None
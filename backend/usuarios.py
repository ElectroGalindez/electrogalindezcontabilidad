import json
import bcrypt
from pathlib import Path
from datetime import datetime

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

def crear_usuario(username, password, rol="empleado"):
    usuarios = cargar_usuarios()
    if any(u["username"] == username for u in usuarios):
        raise ValueError("El usuario ya existe.")
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    nuevo = {
        "username": username,
        "password": hashed,
        "rol": rol,
        "activo": True,
        "created_at": datetime.now().isoformat()
    }
    usuarios.append(nuevo)
    guardar_usuarios(usuarios)
    return nuevo

def autenticar_usuario(username, password):
    usuarios = cargar_usuarios()
    for u in usuarios:
        if u["username"] == username and u["activo"]:
            if bcrypt.checkpw(password.encode(), u["password"].encode()):
                return u
    return None

def cambiar_password(username, new_password):
    usuarios = cargar_usuarios()
    for u in usuarios:
        if u["username"] == username:
            u["password"] = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            guardar_usuarios(usuarios)
            return True
    return False

def cambiar_rol(username, nuevo_rol):
    usuarios = cargar_usuarios()
    for u in usuarios:
        if u["username"] == username:
            u["rol"] = nuevo_rol
            guardar_usuarios(usuarios)
            return True
    return False

def desactivar_usuario(username):
    usuarios = cargar_usuarios()
    for u in usuarios:
        if u["username"] == username:
            u["activo"] = False
            guardar_usuarios(usuarios)
            return True
    return False

def listar_usuarios():
    return cargar_usuarios()

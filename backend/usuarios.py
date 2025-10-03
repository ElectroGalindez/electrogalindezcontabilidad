# backend/usuarios.py
from sqlalchemy import text
from backend.db import engine
import uuid
import bcrypt
from datetime import datetime, timedelta

def generar_id():
    return str(uuid.uuid4())[:8]

# =============================
# CREAR USUARIO
# =============================
def crear_usuario(username, password, rol="empleado"):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    created_at = datetime.now()
    usuario_id = generar_id()
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO usuarios (id, username, password, rol, activo, created_at, requiere_cambio_password, intentos_fallidos, bloqueado_hasta) "
                "VALUES (:id, :username, :password, :rol, TRUE, :created_at, TRUE, 0, NULL)"
            ),
            {"id": usuario_id, "username": username, "password": hashed, "rol": rol, "created_at": created_at}
        )
    return get_usuario(username)

# =============================
# OBTENER USUARIO
# =============================
def get_usuario(username):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM usuarios WHERE username = :username"),
            {"username": username}
        ).fetchone()
        return dict(result) if result else None

# =============================
# AUTENTICAR USUARIO
# =============================
def autenticar_usuario(username, password, max_intentos=5, bloqueo_min=15):
    usuario = get_usuario(username)
    if not usuario or not usuario["activo"]:
        return None

    # Verificar bloqueo
    if usuario.get("bloqueado_hasta"):
        bloqueado_hasta = usuario["bloqueado_hasta"]
        if bloqueado_hasta > datetime.now():
            return {"bloqueado": True, "bloqueado_hasta": bloqueado_hasta.isoformat()}

    # Verificar contraseña
    if bcrypt.checkpw(password.encode(), usuario["password"].encode()):
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE usuarios SET intentos_fallidos=0, bloqueado_hasta=NULL WHERE id=:id"),
                {"id": usuario["id"]}
            )
        return usuario
    else:
        # Incrementar intentos fallidos
        with engine.begin() as conn:
            conn.execute(
                text(
                    "UPDATE usuarios SET intentos_fallidos = intentos_fallidos + 1 "
                    "WHERE id = :id"
                ),
                {"id": usuario["id"]}
            )
        # Releer usuario
        usuario = get_usuario(username)
        if usuario["intentos_fallidos"] >= max_intentos:
            bloqueado_hasta = datetime.now() + timedelta(minutes=bloqueo_min)
            with engine.begin() as conn:
                conn.execute(
                    text("UPDATE usuarios SET bloqueado_hasta = :bloqueado_hasta WHERE id = :id"),
                    {"bloqueado_hasta": bloqueado_hasta, "id": usuario["id"]}
                )
            return {"bloqueado": True, "bloqueado_hasta": bloqueado_hasta.isoformat()}
        return None

# =============================
# CAMBIAR PASSWORD
# =============================
def cambiar_password(username, new_password):
    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE usuarios SET password=:password, requiere_cambio_password=FALSE WHERE username=:username"
            ),
            {"password": hashed, "username": username}
        )
    return True

# =============================
# LISTAR USUARIOS
# =============================
def listar_usuarios():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM usuarios ORDER BY username"))
        return [dict(r) for r in result]

# =============================
# CAMBIAR ROL
# =============================
def cambiar_rol(username, nuevo_rol):
    with engine.begin() as conn:
        conn.execute(text("UPDATE usuarios SET rol=:rol WHERE username=:username"),
                     {"rol": nuevo_rol, "username": username})
    return True

# =============================
# DESACTIVAR USUARIO
# =============================
def desactivar_usuario(username):
    with engine.begin() as conn:
        conn.execute(text("UPDATE usuarios SET activo=FALSE WHERE username=:username"),
                     {"username": username})
    return True

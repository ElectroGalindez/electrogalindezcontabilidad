# backend/usuarios.py

from datetime import datetime, timedelta
import bcrypt
from backend.db import engine, text
from .logs import registrar_log

# =============================
# Funciones de usuarios con SQLAlchemy
# =============================

# Crear usuario
def crear_usuario(username, password, rol="empleado", actor=None):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        with engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO usuarios (username, password, rol)
                    VALUES (:username, :password, :rol)
                """),
                {"username": username, "password": hashed, "rol": rol}
            )
        registrar_log(usuario=actor or username, accion="crear_usuario",
                      detalles={"username": username, "rol": rol})
        return {"username": username, "rol": rol}
    except Exception as e:
        raise ValueError("El usuario ya existe o hubo un error en la base de datos.") from e

# Autenticar usuario
def autenticar_usuario(username, password, max_intentos=5, bloqueo_min=15):
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT password, activo, intentos_fallidos, bloqueado_hasta, rol FROM usuarios WHERE username=:username"),
            {"username": username}
        ).fetchone()

        if not row:
            return None

        hashed, activo, intentos, bloqueado_hasta, rol = row

        if not activo:
            return None

        if bloqueado_hasta and bloqueado_hasta > datetime.now():
            return {"bloqueado": True, "bloqueado_hasta": bloqueado_hasta.isoformat()}

        if bcrypt.checkpw(password.encode(), hashed.encode()):
            conn.execute(
                text("UPDATE usuarios SET intentos_fallidos=0, bloqueado_hasta=NULL WHERE username=:username"),
                {"username": username}
            )
            return {"username": username, "rol": rol}
        else:
            intentos = (intentos or 0) + 1
            bloqueado = None
            if intentos >= max_intentos:
                bloqueado = datetime.now() + timedelta(minutes=bloqueo_min)
                conn.execute(
                    text("UPDATE usuarios SET intentos_fallidos=:intentos, bloqueado_hasta=:bloqueado WHERE username=:username"),
                    {"intentos": intentos, "bloqueado": bloqueado, "username": username}
                )
                registrar_log(usuario=username, accion="bloqueo_usuario",
                              detalles={"motivo": "demasiados intentos fallidos", "bloqueado_hasta": bloqueado.isoformat()})
            else:
                conn.execute(
                    text("UPDATE usuarios SET intentos_fallidos=:intentos WHERE username=:username"),
                    {"intentos": intentos, "username": username}
                )
            return None

# Cambiar contraseña
def cambiar_password(username, new_password, actor=None):
    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    with engine.connect() as conn:
        conn.execute(
            text("UPDATE usuarios SET password=:password, requiere_cambio_password=FALSE WHERE username=:username"),
            {"password": hashed, "username": username}
        )
    registrar_log(usuario=actor or username, accion="cambiar_password", detalles={"username": username})
    return True

# Cambiar rol
def cambiar_rol(username, nuevo_rol, actor=None):
    old_rol = get_rol(username)
    with engine.connect() as conn:
        conn.execute(
            text("UPDATE usuarios SET rol=:rol WHERE username=:username"),
            {"rol": nuevo_rol, "username": username}
        )
    registrar_log(usuario=actor or username, accion="cambiar_rol",
                  detalles={"username": username, "rol_anterior": old_rol, "rol_nuevo": nuevo_rol})
    return True

# Desactivar usuario
def desactivar_usuario(username, actor=None):
    with engine.connect() as conn:
        conn.execute(
            text("UPDATE usuarios SET activo=FALSE WHERE username=:username"),
            {"username": username}
        )
    registrar_log(usuario=actor or username, accion="desactivar_usuario", detalles={"username": username})
    return True
# Activar usuario
def activar_usuario(username, actor=None):
    with engine.connect() as conn:
        conn.execute(
            text("UPDATE usuarios SET activo=TRUE WHERE username=:username"),
            {"username": username}
        )
    registrar_log(usuario=actor or username, accion="activar_usuario", detalles={"username": username})
    return True

# Listar usuarios
def listar_usuarios():
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT username, rol, activo, created_at, requiere_cambio_password FROM usuarios ORDER BY created_at")
        ).fetchall()
    usuarios = []
    for r in rows:
        usuarios.append({
            "username": r[0],
            "rol": r[1],
            "activo": r[2],
            "created_at": r[3].isoformat() if r[3] else None,
            "requiere_cambio_password": r[4]
        })
    return usuarios

# Revisar si requiere cambio de contraseña
def requiere_cambio_password(username):
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT requiere_cambio_password FROM usuarios WHERE username=:username"),
            {"username": username}
        ).fetchone()
    return row[0] if row else False

# Obtener rol
def get_rol(username):
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT rol FROM usuarios WHERE username=:username"),
            {"username": username}
        ).fetchone()
    return row[0] if row else None

# Obtener logs de un usuario
def obtener_logs_usuario(username):
    from .logs import obtener_logs_usuario as fetch_logs
    return fetch_logs(username)
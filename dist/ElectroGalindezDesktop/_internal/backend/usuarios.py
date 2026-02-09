"""User management helpers."""

from datetime import datetime, timedelta

import bcrypt

from .db import get_connection
from .logs import registrar_log


def crear_usuario(username, password, rol="empleado", actor=None):
    """Crear un usuario con contraseña encriptada."""
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    query = """
        INSERT INTO usuarios (username, password, rol)
        VALUES (:username, :password, :rol)
    """
    try:
        with get_connection() as conn:
            conn.execute(query, {"username": username, "password": hashed, "rol": rol})
        registrar_log(usuario=actor or username, accion="crear_usuario", detalles={"username": username, "rol": rol})
        return {"username": username, "rol": rol}
    except Exception as exc:
        raise ValueError(f"Error al crear usuario ({username}): {exc}")


def autenticar_usuario(username, password, max_intentos=5, bloqueo_min=15):
    """Autenticar usuario y manejar intentos fallidos con bloqueo temporal."""
    now = datetime.now()
    q_select = """
        SELECT password, activo, intentos_fallidos, bloqueado_hasta, rol
        FROM usuarios WHERE username=:username
    """
    q_reset = """
        UPDATE usuarios
        SET intentos_fallidos=0, bloqueado_hasta=NULL
        WHERE username=:username
    """
    q_update = """
        UPDATE usuarios
        SET intentos_fallidos=:intentos, bloqueado_hasta=:bloqueado
        WHERE username=:username
    """

    with get_connection() as conn:
        row = conn.execute(q_select, {"username": username}).fetchone()
        if not row or not row["activo"]:
            return None

        if row["bloqueado_hasta"]:
            bloqueado_hasta = datetime.fromisoformat(row["bloqueado_hasta"])
            if bloqueado_hasta > now:
                return {"bloqueado": True, "bloqueado_hasta": bloqueado_hasta.isoformat()}

        if bcrypt.checkpw(password.encode(), row["password"].encode()):
            if row["intentos_fallidos"] or row["bloqueado_hasta"]:
                conn.execute(q_reset, {"username": username})
            return {"username": username, "rol": row["rol"]}

        intentos = (row["intentos_fallidos"] or 0) + 1
        bloqueado = None
        if intentos >= max_intentos:
            bloqueado = now + timedelta(minutes=bloqueo_min)
            registrar_log(
                usuario=username,
                accion="bloqueo_usuario",
                detalles={"motivo": "intentos fallidos", "bloqueado_hasta": bloqueado.isoformat()},
            )
        conn.execute(q_update, {"intentos": intentos, "bloqueado": bloqueado, "username": username})
    return None


def login(username, password):
    """Alias para autenticar_usuario (compatibilidad con UI)."""
    return autenticar_usuario(username, password)


def cambiar_password(username, new_password, actor=None):
    """Actualizar la contraseña de un usuario."""
    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    with get_connection() as conn:
        conn.execute(
            "UPDATE usuarios SET password=:p, requiere_cambio_password=0 WHERE username=:u",
            {"p": hashed, "u": username},
        )
    registrar_log(usuario=actor or username, accion="cambiar_password", detalles={"username": username})
    return True


def cambiar_rol(username, nuevo_rol, actor=None):
    """Actualizar el rol asignado a un usuario."""
    old_rol = get_rol(username)
    with get_connection() as conn:
        conn.execute(
            "UPDATE usuarios SET rol=:r WHERE username=:u",
            {"r": nuevo_rol, "u": username},
        )
    registrar_log(
        usuario=actor or username,
        accion="cambiar_rol",
        detalles={"username": username, "rol_anterior": old_rol, "rol_nuevo": nuevo_rol},
    )
    return True


def set_estado_usuario(username, activo: bool, actor=None):
    """Activar o desactivar un usuario."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE usuarios SET activo=:a WHERE username=:u",
            {"a": int(activo), "u": username},
        )
    accion = "activar_usuario" if activo else "desactivar_usuario"
    registrar_log(usuario=actor or username, accion=accion, detalles={"username": username})
    return True


def listar_usuarios():
    """Listar usuarios registrados."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT username, rol, activo, created_at, requiere_cambio_password
            FROM usuarios ORDER BY created_at DESC
        """
        ).fetchall()
    return [
        {
            "username": r["username"],
            "rol": r["rol"],
            "activo": r["activo"],
            "created_at": r["created_at"],
            "requiere_cambio_password": r["requiere_cambio_password"],
        }
        for r in rows
    ]


def requiere_cambio_password(username):
    """Indicar si el usuario debe cambiar su contraseña."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT requiere_cambio_password FROM usuarios WHERE username=:u",
            {"u": username},
        ).fetchone()
    row_val = row[0] if row else 0
    return bool(row_val)


def get_rol(username):
    """Obtener el rol asociado a un usuario."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT rol FROM usuarios WHERE username=:u",
            {"u": username},
        ).fetchone()
    return row[0] if row else None


def obtener_logs_usuario(username):
    """Obtener el historial de acciones de un usuario."""
    from .logs import obtener_logs_usuario as fetch_logs

    return fetch_logs(username)


def activar_usuario(username, actor=None):
    """Activar un usuario."""
    return set_estado_usuario(username, True, actor)


def desactivar_usuario(username, actor=None):
    """Desactivar un usuario."""
    return set_estado_usuario(username, False, actor)


def eliminar_usuario(username, actor=None):
    """Eliminar un usuario de la base de datos."""
    with get_connection() as conn:
        conn.execute("DELETE FROM usuarios WHERE username=:u", {"u": username})
    registrar_log(usuario=actor or username, accion="eliminar_usuario", detalles={"username": username})
    return True

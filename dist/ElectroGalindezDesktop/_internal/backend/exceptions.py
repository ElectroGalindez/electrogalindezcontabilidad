"""Custom exceptions that log audit entries."""

from .logs import registrar_log


class NotFoundError(Exception):
    """Error raised when an entity is not found."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        registrar_log(
            usuario=kwargs.get("actor", "sistema"),
            accion="exception_NotFoundError",
            detalles={"mensaje": str(args[0]) if args else ""},
        )


class ValidationError(Exception):
    """Error raised when validation fails."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        registrar_log(
            usuario=kwargs.get("actor", "sistema"),
            accion="exception_ValidationError",
            detalles={"mensaje": str(args[0]) if args else ""},
        )


class InsufficientStockError(Exception):
    """Error raised when product stock is insufficient."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        registrar_log(
            usuario=kwargs.get("actor", "sistema"),
            accion="exception_InsufficientStockError",
            detalles={"mensaje": str(args[0]) if args else ""},
        )

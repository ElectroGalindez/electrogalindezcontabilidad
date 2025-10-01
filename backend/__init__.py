# backend/__init__.py
# Exportar funciones comunes para facilidad de import
from . import productos, clientes, ventas, deudas, utils, usuarios

# Exportar funciones clave de usuarios
from .usuarios import requiere_cambio_password

__all__ = [
	"productos",
	"clientes",
	"ventas",
	"deudas",
	"utils",
	"usuarios",
	"requiere_cambio_password"
]

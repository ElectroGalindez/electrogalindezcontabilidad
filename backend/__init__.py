# Permite importar módulos desde backend
from .db import engine, MetaData
from .usuarios import crear_usuario, autenticar_usuario, cambiar_password, requiere_cambio_password, activar_usuario, desactivar_usuario,  obtener_logs_usuario
from .productos import list_products, get_product, agregar_producto, editar_producto, eliminar_producto
from .clientes import list_clients, get_client, add_client, edit_client, delete_client, update_client
from .ventas import list_sales, get_sale, delete_sale, register_sale
from .deudas import list_debts, get_debt
from .logs import registrar_log

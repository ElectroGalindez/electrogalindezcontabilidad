"""Public backend API re-exports for the Streamlit UI."""

from .categorias import (
    agregar_categoria,
    editar_categoria,
    eliminar_categoria,
    get_category,
    list_categories,
    list_products_by_category,
)
from .clientes import (
    add_client,
    delete_client,
    edit_client,
    get_client,
    list_clients,
    update_client,
)
from .db import get_connection
from .deudas import (
    add_debt,
    debts_by_client,
    delete_debt,
    get_debt,
    list_clientes_con_deuda,
    list_debts,
    list_detalle_deudas,
    pay_debt_producto,
    update_debt,
)
from .logs import registrar_log
from .notas import add_note, delete_note, list_notes, update_note
from .productos import (
    adjust_stock,
    editar_producto,
    eliminar_producto,
    get_product,
    guardar_producto,
    list_products,
    update_product,
)
from .usuarios import (
    activar_usuario,
    autenticar_usuario,
    cambiar_password,
    crear_usuario,
    desactivar_usuario,
    eliminar_usuario,
    obtener_logs_usuario,
    requiere_cambio_password,
)
from .ventas import (
    delete_sale,
    editar_venta_extra,
    generar_factura_pdf,
    get_sale,
    list_sales,
    listar_ventas_dict,
    register_sale,
)

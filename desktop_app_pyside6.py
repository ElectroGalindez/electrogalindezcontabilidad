import json
import sys
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QPlainTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from backend import productos, ventas, usuarios
from backend.usuarios import set_estado_usuario
from backend import notas as notas_backend


def show_error(parent: QWidget, message: str) -> None:
    QMessageBox.critical(parent, "Error", message)


def show_info(parent: QWidget, message: str) -> None:
    QMessageBox.information(parent, "Información", message)


class UsuariosTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Usuario", "Rol", "Activo", "Creado", "Requiere cambio password"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)

        form_box = QGroupBox("Administrar usuarios")
        form_layout = QFormLayout(form_box)
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.rol = QComboBox()
        self.rol.addItems(["empleado", "admin"])
        self.activo = QCheckBox("Activo")
        self.activo.setChecked(True)

        form_layout.addRow("Usuario", self.username)
        form_layout.addRow("Contraseña (opcional para actualizar)", self.password)
        form_layout.addRow("Rol", self.rol)
        form_layout.addRow("", self.activo)
        layout.addWidget(form_box)

        button_layout = QHBoxLayout()
        btn_create = QPushButton("Crear")
        btn_update = QPushButton("Actualizar")
        btn_delete = QPushButton("Eliminar")
        btn_refresh = QPushButton("Refrescar")
        button_layout.addWidget(btn_create)
        button_layout.addWidget(btn_update)
        button_layout.addWidget(btn_delete)
        button_layout.addWidget(btn_refresh)
        layout.addLayout(button_layout)

        btn_create.clicked.connect(self.create_user)
        btn_update.clicked.connect(self.update_user)
        btn_delete.clicked.connect(self.delete_user)
        btn_refresh.clicked.connect(self.load_users)

        self.load_users()

    def load_users(self) -> None:
        data = usuarios.listar_usuarios()
        self.table.setRowCount(0)
        for row in data:
            idx = self.table.rowCount()
            self.table.insertRow(idx)
            self.table.setItem(idx, 0, QTableWidgetItem(row["username"]))
            self.table.setItem(idx, 1, QTableWidgetItem(row["rol"]))
            self.table.setItem(idx, 2, QTableWidgetItem("Sí" if row["activo"] else "No"))
            self.table.setItem(idx, 3, QTableWidgetItem(str(row.get("created_at") or "")))
            self.table.setItem(idx, 4, QTableWidgetItem("Sí" if row["requiere_cambio_password"] else "No"))

    def create_user(self) -> None:
        try:
            usuarios.crear_usuario(
                self.username.text().strip(),
                self.password.text(),
                self.rol.currentText(),
            )
            show_info(self, "Usuario creado correctamente.")
            self.load_users()
        except Exception as exc:
            show_error(self, str(exc))

    def update_user(self) -> None:
        username = self.username.text().strip()
        if not username:
            show_error(self, "Debes indicar un usuario para actualizar.")
            return
        try:
            usuarios.cambiar_rol(username, self.rol.currentText())
            set_estado_usuario(username, self.activo.isChecked())
            if self.password.text():
                usuarios.cambiar_password(username, self.password.text())
            show_info(self, "Usuario actualizado correctamente.")
            self.load_users()
        except Exception as exc:
            show_error(self, str(exc))

    def delete_user(self) -> None:
        username = self.username.text().strip()
        if not username:
            show_error(self, "Debes indicar un usuario para eliminar.")
            return
        try:
            usuarios.eliminar_usuario(username)
            show_info(self, "Usuario eliminado correctamente.")
            self.load_users()
        except Exception as exc:
            show_error(self, str(exc))


class InventarioTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Precio", "Cantidad", "Categoría ID"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)

        form_box = QGroupBox("Administrar productos")
        form_layout = QFormLayout(form_box)
        self.product_id = QSpinBox()
        self.product_id.setMaximum(10**9)
        self.nombre = QLineEdit()
        self.precio = QDoubleSpinBox()
        self.precio.setMaximum(10**9)
        self.precio.setDecimals(2)
        self.cantidad = QSpinBox()
        self.cantidad.setMaximum(10**9)
        self.categoria_id = QSpinBox()
        self.categoria_id.setMaximum(10**9)

        form_layout.addRow("ID (solo editar/eliminar)", self.product_id)
        form_layout.addRow("Nombre", self.nombre)
        form_layout.addRow("Precio", self.precio)
        form_layout.addRow("Cantidad", self.cantidad)
        form_layout.addRow("Categoría ID", self.categoria_id)
        layout.addWidget(form_box)

        button_layout = QHBoxLayout()
        btn_create = QPushButton("Crear")
        btn_update = QPushButton("Actualizar")
        btn_delete = QPushButton("Eliminar")
        btn_refresh = QPushButton("Refrescar")
        button_layout.addWidget(btn_create)
        button_layout.addWidget(btn_update)
        button_layout.addWidget(btn_delete)
        button_layout.addWidget(btn_refresh)
        layout.addLayout(button_layout)

        btn_create.clicked.connect(self.create_product)
        btn_update.clicked.connect(self.update_product)
        btn_delete.clicked.connect(self.delete_product)
        btn_refresh.clicked.connect(self.load_products)

        self.load_products()

    def load_products(self) -> None:
        data = productos.list_products()
        self.table.setRowCount(0)
        for row in data:
            idx = self.table.rowCount()
            self.table.insertRow(idx)
            self.table.setItem(idx, 0, QTableWidgetItem(str(row["id"])))
            self.table.setItem(idx, 1, QTableWidgetItem(row["nombre"]))
            self.table.setItem(idx, 2, QTableWidgetItem(str(row["precio"])))
            self.table.setItem(idx, 3, QTableWidgetItem(str(row["cantidad"])))
            self.table.setItem(idx, 4, QTableWidgetItem(str(row.get("categoria_id") or "")))

    def create_product(self) -> None:
        try:
            productos.guardar_producto(
                nombre=self.nombre.text(),
                precio=float(self.precio.value()),
                cantidad=int(self.cantidad.value()),
                categoria_id=str(self.categoria_id.value()),
            )
            show_info(self, "Producto creado/actualizado correctamente.")
            self.load_products()
        except Exception as exc:
            show_error(self, str(exc))

    def update_product(self) -> None:
        if not self.product_id.value():
            show_error(self, "Debes indicar un ID de producto para actualizar.")
            return
        try:
            productos.editar_producto(
                producto_id=str(self.product_id.value()),
                nombre=self.nombre.text(),
                precio=float(self.precio.value()),
                cantidad=int(self.cantidad.value()),
                categoria_id=str(self.categoria_id.value()),
            )
            show_info(self, "Producto actualizado correctamente.")
            self.load_products()
        except Exception as exc:
            show_error(self, str(exc))

    def delete_product(self) -> None:
        if not self.product_id.value():
            show_error(self, "Debes indicar un ID de producto para eliminar.")
            return
        try:
            productos.eliminar_producto(self.product_id.value())
            show_info(self, "Producto eliminado correctamente.")
            self.load_products()
        except Exception as exc:
            show_error(self, str(exc))


class VentasTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Cliente ID", "Total", "Pagado", "Usuario", "Tipo pago", "Fecha"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)

        form_box = QGroupBox("Registrar venta")
        form_layout = QFormLayout(form_box)
        self.venta_id = QSpinBox()
        self.venta_id.setMaximum(10**9)
        self.cliente_id = QSpinBox()
        self.cliente_id.setMaximum(10**9)
        self.total = QDoubleSpinBox()
        self.total.setMaximum(10**9)
        self.total.setDecimals(2)
        self.pagado = QDoubleSpinBox()
        self.pagado.setMaximum(10**9)
        self.pagado.setDecimals(2)
        self.usuario = QLineEdit()
        self.tipo_pago = QLineEdit()
        self.productos_json = QPlainTextEdit()
        self.productos_json.setPlaceholderText('[{"id_producto":1,"nombre":"Producto","cantidad":1,"precio_unitario":10}]')

        form_layout.addRow("ID (editar extra/eliminar)", self.venta_id)
        form_layout.addRow("Cliente ID", self.cliente_id)
        form_layout.addRow("Total", self.total)
        form_layout.addRow("Pagado", self.pagado)
        form_layout.addRow("Usuario", self.usuario)
        form_layout.addRow("Tipo de pago", self.tipo_pago)
        form_layout.addRow("Productos (JSON opcional)", self.productos_json)
        layout.addWidget(form_box)

        extra_box = QGroupBox("Actualizar datos adicionales")
        extra_layout = QFormLayout(extra_box)
        self.observaciones = QLineEdit()
        self.vendedor = QLineEdit()
        self.telefono_vendedor = QLineEdit()
        self.chofer = QLineEdit()
        self.chapa = QLineEdit()
        extra_layout.addRow("Observaciones", self.observaciones)
        extra_layout.addRow("Vendedor", self.vendedor)
        extra_layout.addRow("Teléfono vendedor", self.telefono_vendedor)
        extra_layout.addRow("Chofer", self.chofer)
        extra_layout.addRow("Chapa", self.chapa)
        layout.addWidget(extra_box)

        button_layout = QHBoxLayout()
        btn_create = QPushButton("Crear")
        btn_update = QPushButton("Actualizar datos extra")
        btn_delete = QPushButton("Eliminar")
        btn_refresh = QPushButton("Refrescar")
        button_layout.addWidget(btn_create)
        button_layout.addWidget(btn_update)
        button_layout.addWidget(btn_delete)
        button_layout.addWidget(btn_refresh)
        layout.addLayout(button_layout)

        btn_create.clicked.connect(self.create_sale)
        btn_update.clicked.connect(self.update_sale_extra)
        btn_delete.clicked.connect(self.delete_sale)
        btn_refresh.clicked.connect(self.load_sales)

        self.load_sales()

    def load_sales(self) -> None:
        data = ventas.list_sales()
        self.table.setRowCount(0)
        for row in data:
            idx = self.table.rowCount()
            self.table.insertRow(idx)
            self.table.setItem(idx, 0, QTableWidgetItem(str(row["id"])))
            self.table.setItem(idx, 1, QTableWidgetItem(str(row.get("cliente_id") or "")))
            self.table.setItem(idx, 2, QTableWidgetItem(str(row.get("total") or "")))
            self.table.setItem(idx, 3, QTableWidgetItem(str(row.get("pagado") or "")))
            self.table.setItem(idx, 4, QTableWidgetItem(str(row.get("usuario") or "")))
            self.table.setItem(idx, 5, QTableWidgetItem(str(row.get("tipo_pago") or "")))
            self.table.setItem(idx, 6, QTableWidgetItem(str(row.get("fecha") or "")))

    def _parse_productos(self) -> Optional[list]:
        contenido = self.productos_json.toPlainText().strip()
        if not contenido:
            return None
        try:
            data = json.loads(contenido)
        except json.JSONDecodeError as exc:
            raise ValueError(f"JSON inválido en productos: {exc}") from exc
        if not isinstance(data, list):
            raise ValueError("El JSON de productos debe ser una lista.")
        return data

    def create_sale(self) -> None:
        try:
            productos_data = self._parse_productos()
            ventas.register_sale(
                cliente_id=int(self.cliente_id.value()),
                total=float(self.total.value()),
                pagado=float(self.pagado.value()),
                usuario=self.usuario.text().strip(),
                tipo_pago=self.tipo_pago.text().strip(),
                productos=productos_data,
            )
            show_info(self, "Venta registrada correctamente.")
            self.load_sales()
        except Exception as exc:
            show_error(self, str(exc))

    def update_sale_extra(self) -> None:
        if not self.venta_id.value():
            show_error(self, "Debes indicar el ID de la venta para actualizar.")
            return
        try:
            ventas.editar_venta_extra(
                sale_id=str(self.venta_id.value()),
                observaciones=self.observaciones.text() or None,
                vendedor=self.vendedor.text() or None,
                telefono_vendedor=self.telefono_vendedor.text() or None,
                chofer=self.chofer.text() or None,
                chapa=self.chapa.text() or None,
            )
            show_info(self, "Venta actualizada correctamente.")
            self.load_sales()
        except Exception as exc:
            show_error(self, str(exc))

    def delete_sale(self) -> None:
        if not self.venta_id.value():
            show_error(self, "Debes indicar el ID de la venta para eliminar.")
            return
        try:
            ventas.delete_sale(str(self.venta_id.value()))
            show_info(self, "Venta eliminada correctamente.")
            self.load_sales()
        except Exception as exc:
            show_error(self, str(exc))


class NotasTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["ID", "Contenido", "Fecha"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)

        form_box = QGroupBox("Administrar notas")
        form_layout = QFormLayout(form_box)
        self.nota_id = QSpinBox()
        self.nota_id.setMaximum(10**9)
        self.contenido = QPlainTextEdit()
        form_layout.addRow("ID (editar/eliminar)", self.nota_id)
        form_layout.addRow("Contenido", self.contenido)
        layout.addWidget(form_box)

        button_layout = QHBoxLayout()
        btn_create = QPushButton("Crear")
        btn_update = QPushButton("Actualizar")
        btn_delete = QPushButton("Eliminar")
        btn_refresh = QPushButton("Refrescar")
        button_layout.addWidget(btn_create)
        button_layout.addWidget(btn_update)
        button_layout.addWidget(btn_delete)
        button_layout.addWidget(btn_refresh)
        layout.addLayout(button_layout)

        btn_create.clicked.connect(self.create_note)
        btn_update.clicked.connect(self.update_note)
        btn_delete.clicked.connect(self.delete_note)
        btn_refresh.clicked.connect(self.load_notes)

        self.load_notes()

    def load_notes(self) -> None:
        data = notas_backend.list_notes()
        self.table.setRowCount(0)
        for row in data:
            idx = self.table.rowCount()
            self.table.insertRow(idx)
            self.table.setItem(idx, 0, QTableWidgetItem(str(row["id"])))
            self.table.setItem(idx, 1, QTableWidgetItem(row["contenido"]))
            self.table.setItem(idx, 2, QTableWidgetItem(str(row["fecha"])))

    def create_note(self) -> None:
        try:
            notas_backend.add_note(self.contenido.toPlainText())
            show_info(self, "Nota creada correctamente.")
            self.load_notes()
        except Exception as exc:
            show_error(self, str(exc))

    def update_note(self) -> None:
        if not self.nota_id.value():
            show_error(self, "Debes indicar el ID de la nota para actualizar.")
            return
        try:
            notas_backend.update_note(self.nota_id.value(), self.contenido.toPlainText())
            show_info(self, "Nota actualizada correctamente.")
            self.load_notes()
        except Exception as exc:
            show_error(self, str(exc))

    def delete_note(self) -> None:
        if not self.nota_id.value():
            show_error(self, "Debes indicar el ID de la nota para eliminar.")
            return
        try:
            notas_backend.delete_note(self.nota_id.value())
            show_info(self, "Nota eliminada correctamente.")
            self.load_notes()
        except Exception as exc:
            show_error(self, str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ElectroGalíndez - Gestión (PySide6)")
        self.resize(1200, 800)

        tabs = QTabWidget()
        tabs.addTab(UsuariosTab(), "Usuarios")
        tabs.addTab(InventarioTab(), "Inventario")
        tabs.addTab(VentasTab(), "Ventas")
        tabs.addTab(NotasTab(), "Notas")
        self.setCentralWidget(tabs)


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

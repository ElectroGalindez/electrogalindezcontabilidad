import os
import sys

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenuBar,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pyside6_login_tab import LoginTab
from pyside6_dashboard_tab import DashboardTab
from pyside6_usuarios_tab import UsuariosTab


class InventarioTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Stock", "Precio"])
        layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        btn_add = QPushButton("Agregar Producto")
        btn_edit = QPushButton("Editar Producto")
        btn_delete = QPushButton("Eliminar Producto")
        btn_add.clicked.connect(lambda: print("Agregar Producto presionado"))
        btn_edit.clicked.connect(lambda: print("Editar Producto presionado"))
        btn_delete.clicked.connect(lambda: print("Eliminar Producto presionado"))
        button_layout.addWidget(btn_add)
        button_layout.addWidget(btn_edit)
        button_layout.addWidget(btn_delete)
        layout.addLayout(button_layout)


class VentasTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        cliente_layout = QFormLayout()
        self.cliente_combo = QComboBox()
        self.cliente_combo.addItem("Seleccione cliente")
        cliente_layout.addRow(QLabel("Cliente"), self.cliente_combo)
        layout.addLayout(cliente_layout)

        productos_layout = QVBoxLayout()
        productos_layout.addWidget(QLabel("Productos"))
        for nombre in ["Producto A", "Producto B", "Producto C"]:
            row = QHBoxLayout()
            row.addWidget(QLabel(nombre))
            qty = QSpinBox()
            qty.setMinimum(0)
            row.addWidget(qty)
            productos_layout.addLayout(row)
        layout.addLayout(productos_layout)

        self.total_label = QLabel("Total: $0.00")
        layout.addWidget(self.total_label)

        self.registrar_button = QPushButton("Registrar Venta")
        self.registrar_button.clicked.connect(self._handle_registrar)
        layout.addWidget(self.registrar_button)

    def _handle_registrar(self) -> None:
        print("Registrar Venta presionado")


class ClientesTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Teléfono", "Email"])
        layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        btn_add = QPushButton("Agregar")
        btn_edit = QPushButton("Editar")
        btn_delete = QPushButton("Eliminar")
        btn_add.clicked.connect(lambda: print("Agregar cliente presionado"))
        btn_edit.clicked.connect(lambda: print("Editar cliente presionado"))
        btn_delete.clicked.connect(lambda: print("Eliminar cliente presionado"))
        button_layout.addWidget(btn_add)
        button_layout.addWidget(btn_edit)
        button_layout.addWidget(btn_delete)
        layout.addLayout(button_layout)


class DeudasTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Cliente", "Monto", "Fecha", "Estado"])
        layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        btn_paid = QPushButton("Marcar como Pagado")
        btn_add = QPushButton("Agregar Deuda")
        btn_paid.clicked.connect(lambda: print("Marcar como Pagado presionado"))
        btn_add.clicked.connect(lambda: print("Agregar Deuda presionado"))
        button_layout.addWidget(btn_paid)
        button_layout.addWidget(btn_add)
        layout.addLayout(button_layout)


class CategoriasTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre"])
        layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        btn_add = QPushButton("Agregar")
        btn_edit = QPushButton("Editar")
        btn_delete = QPushButton("Eliminar")
        btn_add.clicked.connect(lambda: print("Agregar categoría presionado"))
        btn_edit.clicked.connect(lambda: print("Editar categoría presionado"))
        btn_delete.clicked.connect(lambda: print("Eliminar categoría presionado"))
        button_layout.addWidget(btn_add)
        button_layout.addWidget(btn_edit)
        button_layout.addWidget(btn_delete)
        layout.addLayout(button_layout)


class LogsTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Usuario", "Acción", "Fecha"])
        layout.addWidget(self.table)


class HistorialTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Usuario", "Acción", "Detalle", "Fecha"])
        layout.addWidget(self.table)

    def load_historial(self) -> None:
        from backend import historial
        from PySide6.QtWidgets import QMessageBox

        try:
            acciones = historial.listar_acciones()
            self.table.setRowCount(0)
            self.table.setRowCount(len(acciones))
            for row_index, accion in enumerate(acciones):
                detalle = accion.get("detalle", accion.get("detalles", ""))
                valores = [
                    accion.get("id", ""),
                    accion.get("usuario", ""),
                    accion.get("accion", ""),
                    detalle,
                    accion.get("fecha", ""),
                ]
                for col_index, valor in enumerate(valores):
                    item = QTableWidgetItem(str(valor))
                    self.table.setItem(row_index, col_index, item)
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ElectroGalindez")
        self.resize(1200, 800)
        self._set_icon()

        tabs = QTabWidget()
        tabs.addTab(LoginTab(), "Login")
        tabs.addTab(DashboardTab(), "Dashboard")
        tabs.addTab(UsuariosTab(), "Usuarios")
        tabs.addTab(InventarioTab(), "Inventario")
        tabs.addTab(VentasTab(), "Ventas")
        tabs.addTab(ClientesTab(), "Clientes")
        tabs.addTab(DeudasTab(), "Deudas")
        tabs.addTab(CategoriasTab(), "Categorías")
        tabs.addTab(LogsTab(), "Logs")
        tabs.addTab(HistorialTab(), "Historial de Acciones")
        self.setCentralWidget(tabs)

        self._build_menu()

    def _set_icon(self) -> None:
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def _build_menu(self) -> None:
        menu = self.menuBar().addMenu("Archivo")
        salir_action = QAction("Salir", self)
        salir_action.triggered.connect(self.close)
        menu.addAction(salir_action)


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

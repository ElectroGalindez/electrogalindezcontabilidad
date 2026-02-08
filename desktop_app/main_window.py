from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QMainWindow, QTabWidget

from .clientes_widget import ClientesWidget
from .dashboard_widget import DashboardWidget
from .deudas_widget import DeudasWidget
from .historial_widget import HistorialWidget
from .inventario_widget import InventarioWidget
from .logs_widget import LogsWidget
from .usuarios_widget import UsuariosWidget
from .ventas_widget import VentasWidget


class MainWindow(QMainWindow):
    """Ventana principal con pestañas para cada módulo."""

    def __init__(self, current_user: Optional[dict] = None) -> None:
        super().__init__()
        self.current_user = current_user or {}
        self.setWindowTitle("ElectroGalíndez | Panel principal")
        self.resize(1200, 760)

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.dashboard_tab = DashboardWidget()
        self.usuarios_tab = UsuariosWidget()
        self.ventas_tab = VentasWidget()
        self.inventario_tab = InventarioWidget()
        self.clientes_tab = ClientesWidget()
        self.deudas_tab = DeudasWidget()
        self.logs_tab = LogsWidget()
        self.historial_tab = HistorialWidget()

        self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
        self.tab_widget.addTab(self.usuarios_tab, "Usuarios")
        self.tab_widget.addTab(self.ventas_tab, "Ventas")
        self.tab_widget.addTab(self.inventario_tab, "Inventario")
        self.tab_widget.addTab(self.clientes_tab, "Clientes")
        self.tab_widget.addTab(self.deudas_tab, "Deudas")
        self.tab_widget.addTab(self.logs_tab, "Logs")
        self.tab_widget.addTab(self.historial_tab, "Historial")

        self.statusBar().showMessage("Sesión iniciada")

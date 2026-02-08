import os
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ElectroGalindez")
        self._set_icon()

        tabs = QTabWidget()
        tabs.addTab(QWidget(), "Login")
        tabs.addTab(QWidget(), "Dashboard")
        tabs.addTab(QWidget(), "Usuarios")
        tabs.addTab(QWidget(), "Inventario")
        tabs.addTab(QWidget(), "Ventas")
        tabs.addTab(QWidget(), "Clientes")
        tabs.addTab(QWidget(), "Deudas")
        tabs.addTab(QWidget(), "Categorías")
        tabs.addTab(QWidget(), "Logs")
        tabs.addTab(QWidget(), "Historial de Acciones")

        self.setCentralWidget(tabs)

    def _set_icon(self) -> None:
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

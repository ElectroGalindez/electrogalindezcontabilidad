from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
)


class UsuariosTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Rol", "Estado"])
        layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        btn_add = QPushButton("Agregar")
        btn_edit = QPushButton("Editar")
        btn_delete = QPushButton("Eliminar")

        btn_add.clicked.connect(lambda: print("Botón Agregar presionado"))
        btn_edit.clicked.connect(lambda: print("Botón Editar presionado"))
        btn_delete.clicked.connect(lambda: print("Botón Eliminar presionado"))

        button_layout.addWidget(btn_add)
        button_layout.addWidget(btn_edit)
        button_layout.addWidget(btn_delete)
        layout.addLayout(button_layout)

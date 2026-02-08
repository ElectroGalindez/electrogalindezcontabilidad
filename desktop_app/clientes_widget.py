from __future__ import annotations

from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)


class ClientesWidget(QWidget):
    """Tab de clientes con CRUD."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar cliente")
        self.search_input.textChanged.connect(self.apply_filters)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Buscar:"))
        filter_layout.addWidget(self.search_input)
        filter_layout.addStretch()

        self.add_button = QPushButton("Agregar")
        self.edit_button = QPushButton("Editar")
        self.delete_button = QPushButton("Eliminar")

        self.add_button.clicked.connect(self.on_add)
        self.edit_button.clicked.connect(self.on_edit)
        self.delete_button.clicked.connect(self.on_delete)

        action_layout = QHBoxLayout()
        action_layout.addWidget(self.add_button)
        action_layout.addWidget(self.edit_button)
        action_layout.addWidget(self.delete_button)
        action_layout.addStretch()

        self.table_view = QTableView()
        self.model = QStandardItemModel(0, 5)
        self.model.setHorizontalHeaderLabels(["ID", "Nombre", "Documento", "Teléfono", "Correo"])
        self.table_view.setModel(self.model)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.horizontalHeader().setStretchLastSection(True)

        layout = QVBoxLayout()
        layout.addLayout(filter_layout)
        layout.addLayout(action_layout)
        layout.addWidget(self.table_view)
        self.setLayout(layout)

    def apply_filters(self) -> None:
        """Aplicar filtros de búsqueda en clientes."""
        pass

    def on_add(self) -> None:
        QMessageBox.information(self, "Agregar", "Conecta aquí el alta de clientes.")

    def on_edit(self) -> None:
        QMessageBox.information(self, "Editar", "Conecta aquí la edición de clientes.")

    def on_delete(self) -> None:
        QMessageBox.warning(self, "Eliminar", "Conecta aquí la eliminación de clientes.")

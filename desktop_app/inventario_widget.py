from __future__ import annotations

from PySide6.QtCore import Qt
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
    QComboBox,
)


class InventarioWidget(QWidget):
    """Tab de inventario con filtros y CRUD."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar producto")
        self.search_input.textChanged.connect(self.apply_filters)

        self.category_filter = QComboBox()
        self.category_filter.addItems(["Todas", "Cables", "Iluminación", "Herramientas"])
        self.category_filter.currentIndexChanged.connect(self.apply_filters)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Buscar:"))
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(QLabel("Categoría:"))
        filter_layout.addWidget(self.category_filter)
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
        self.model = QStandardItemModel(0, 6)
        self.model.setHorizontalHeaderLabels(
            ["ID", "Producto", "Categoría", "Stock", "Precio", "Proveedor"]
        )
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
        """Aplicar filtros de búsqueda en inventario."""
        pass

    def on_add(self) -> None:
        QMessageBox.information(self, "Agregar", "Conecta aquí el alta de productos.")

    def on_edit(self) -> None:
        QMessageBox.information(self, "Editar", "Conecta aquí la edición de productos.")

    def on_delete(self) -> None:
        QMessageBox.warning(self, "Eliminar", "Conecta aquí la eliminación de productos.")

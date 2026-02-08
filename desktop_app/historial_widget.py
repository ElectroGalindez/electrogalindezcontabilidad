from __future__ import annotations

from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)


class HistorialWidget(QWidget):
    """Tab de historial de acciones con filtros."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por usuario o acción")
        self.search_input.textChanged.connect(self.apply_filters)

        self.action_filter = QComboBox()
        self.action_filter.addItems(["Todas", "Creación", "Edición", "Eliminación"])
        self.action_filter.currentIndexChanged.connect(self.apply_filters)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Buscar:"))
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(QLabel("Acción:"))
        filter_layout.addWidget(self.action_filter)
        filter_layout.addStretch()

        self.table_view = QTableView()
        self.model = QStandardItemModel(0, 4)
        self.model.setHorizontalHeaderLabels(["Fecha", "Usuario", "Acción", "Detalle"])
        self.table_view.setModel(self.model)
        self.table_view.horizontalHeader().setStretchLastSection(True)

        layout = QVBoxLayout()
        layout.addLayout(filter_layout)
        layout.addWidget(self.table_view)
        self.setLayout(layout)

    def apply_filters(self) -> None:
        """Aplicar filtros de historial."""
        pass

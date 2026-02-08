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


class DeudasWidget(QWidget):
    """Tab de deudas con alertas y marcado de pago."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar cliente o factura")
        self.search_input.textChanged.connect(self.apply_filters)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Buscar:"))
        filter_layout.addWidget(self.search_input)
        filter_layout.addStretch()

        self.mark_paid_button = QPushButton("Marcar pagado")
        self.alert_button = QPushButton("Enviar alerta")

        self.mark_paid_button.clicked.connect(self.on_mark_paid)
        self.alert_button.clicked.connect(self.on_send_alert)

        action_layout = QHBoxLayout()
        action_layout.addWidget(self.mark_paid_button)
        action_layout.addWidget(self.alert_button)
        action_layout.addStretch()

        self.table_view = QTableView()
        self.model = QStandardItemModel(0, 5)
        self.model.setHorizontalHeaderLabels(["Factura", "Cliente", "Monto", "Vencimiento", "Estado"])
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
        """Aplicar filtros de búsqueda en deudas."""
        pass

    def on_mark_paid(self) -> None:
        QMessageBox.information(self, "Pago", "Conecta aquí el marcado de pago.")

    def on_send_alert(self) -> None:
        QMessageBox.warning(self, "Alerta", "Conecta aquí el envío de alertas.")

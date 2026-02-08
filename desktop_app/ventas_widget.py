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


class VentasWidget(QWidget):
    """Tab de ventas con selección de cliente y productos."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.cliente_combo = QComboBox()
        self.cliente_combo.setEditable(True)
        self.cliente_combo.setPlaceholderText("Selecciona cliente")

        self.producto_input = QLineEdit()
        self.producto_input.setPlaceholderText("Buscar producto")

        self.add_product_button = QPushButton("Agregar producto")
        self.add_product_button.clicked.connect(self.on_add_product)

        cliente_layout = QHBoxLayout()
        cliente_layout.addWidget(QLabel("Cliente:"))
        cliente_layout.addWidget(self.cliente_combo)
        cliente_layout.addStretch()

        product_layout = QHBoxLayout()
        product_layout.addWidget(QLabel("Producto:"))
        product_layout.addWidget(self.producto_input)
        product_layout.addWidget(self.add_product_button)
        product_layout.addStretch()

        self.table_view = QTableView()
        self.model = QStandardItemModel(0, 4)
        self.model.setHorizontalHeaderLabels(["Producto", "Cantidad", "Precio", "Subtotal"])
        self.table_view.setModel(self.model)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.horizontalHeader().setStretchLastSection(True)

        self.total_label = QLabel("Total: $0.00")
        self.total_label.setAlignment(Qt.AlignRight)

        self.register_button = QPushButton("Registrar venta")
        self.register_button.clicked.connect(self.on_register_sale)

        footer_layout = QHBoxLayout()
        footer_layout.addWidget(self.total_label)
        footer_layout.addWidget(self.register_button)

        layout = QVBoxLayout()
        layout.addLayout(cliente_layout)
        layout.addLayout(product_layout)
        layout.addWidget(self.table_view)
        layout.addLayout(footer_layout)
        self.setLayout(layout)

    def on_add_product(self) -> None:
        """Agregar producto a la venta (conectar con backend)."""
        QMessageBox.information(self, "Agregar producto", "Conecta aquí la selección de productos.")

    def on_register_sale(self) -> None:
        """Registrar la venta en el backend."""
        QMessageBox.information(self, "Registrar", "Conecta aquí el registro de venta.")

    def recalculate_total(self) -> None:
        """Recalcular el total en función del modelo de productos."""
        pass

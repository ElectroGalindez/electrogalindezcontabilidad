from __future__ import annotations

from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)


class DashboardWidget(QWidget):
    """Tab de dashboard con resumen y gráficas."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.sales_summary = QLabel("Ventas hoy: $0.00")
        self.month_summary = QLabel("Ventas del mes: $0.00")
        self.low_stock_summary = QLabel("Stock bajo: 0 productos")

        summary_box = QGroupBox("Resumen")
        summary_layout = QVBoxLayout()
        summary_layout.addWidget(self.sales_summary)
        summary_layout.addWidget(self.month_summary)
        summary_layout.addWidget(self.low_stock_summary)
        summary_box.setLayout(summary_layout)

        self.chart_sales = QLabel("[Gráfica de ventas]")
        self.chart_sales.setStyleSheet("border: 1px dashed #999; padding: 24px;")

        self.chart_stock = QLabel("[Gráfica de stock]")
        self.chart_stock.setStyleSheet("border: 1px dashed #999; padding: 24px;")

        chart_box = QGroupBox("Gráficas")
        chart_layout = QGridLayout()
        chart_layout.addWidget(self.chart_sales, 0, 0)
        chart_layout.addWidget(self.chart_stock, 0, 1)
        chart_box.setLayout(chart_layout)

        self.low_stock_table = QTableView()
        self.low_stock_model = QStandardItemModel(0, 3)
        self.low_stock_model.setHorizontalHeaderLabels(["Producto", "Stock", "Mínimo"])
        self.low_stock_table.setModel(self.low_stock_model)
        self.low_stock_table.horizontalHeader().setStretchLastSection(True)

        stock_box = QGroupBox("Stock bajo")
        stock_layout = QVBoxLayout()
        stock_layout.addWidget(self.low_stock_table)
        stock_box.setLayout(stock_layout)

        self.refresh_button = QPushButton("Actualizar dashboard")
        self.refresh_button.clicked.connect(self.refresh_data)

        layout = QVBoxLayout()
        layout.addWidget(summary_box)
        layout.addWidget(chart_box)
        layout.addWidget(stock_box)
        layout.addWidget(self.refresh_button)
        self.setLayout(layout)

    def refresh_data(self) -> None:
        """Actualizar datos desde el backend."""
        pass

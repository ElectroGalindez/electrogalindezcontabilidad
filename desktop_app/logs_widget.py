from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)


class LogsWidget(QWidget):
    """Tab de logs con refresco en tiempo real."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.table_view = QTableView()
        self.model = QStandardItemModel(0, 4)
        self.model.setHorizontalHeaderLabels(["Fecha", "Usuario", "Acción", "Detalle"])
        self.table_view.setModel(self.model)
        self.table_view.horizontalHeader().setStretchLastSection(True)

        self.refresh_button = QPushButton("Refrescar ahora")
        self.refresh_button.clicked.connect(self.refresh_data)

        self.toggle_realtime_button = QPushButton("Pausar tiempo real")
        self.toggle_realtime_button.clicked.connect(self.toggle_realtime)

        action_layout = QHBoxLayout()
        action_layout.addWidget(QLabel("Actualización:"))
        action_layout.addWidget(self.refresh_button)
        action_layout.addWidget(self.toggle_realtime_button)
        action_layout.addStretch()

        layout = QVBoxLayout()
        layout.addLayout(action_layout)
        layout.addWidget(self.table_view)
        self.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.setInterval(5000)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start()
        self.realtime_enabled = True

    def refresh_data(self) -> None:
        """Actualizar logs desde el backend."""
        pass

    def toggle_realtime(self) -> None:
        self.realtime_enabled = not self.realtime_enabled
        if self.realtime_enabled:
            self.timer.start()
            self.toggle_realtime_button.setText("Pausar tiempo real")
            QMessageBox.information(self, "Logs", "Refresco en tiempo real activado.")
        else:
            self.timer.stop()
            self.toggle_realtime_button.setText("Reanudar tiempo real")
            QMessageBox.information(self, "Logs", "Refresco en tiempo real pausado.")

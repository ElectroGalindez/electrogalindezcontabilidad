from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class DashboardTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        title = QLabel("Bienvenido a ElectroGalindez")
        layout.addWidget(title)

        figure = Figure(figsize=(5, 3))
        canvas = FigureCanvas(figure)
        ax = figure.add_subplot(111)
        ax.set_title("Ventas del día (placeholder)")
        ax.plot([0, 1, 2], [0, 0, 0])
        ax.set_xlabel("Hora")
        ax.set_ylabel("Ventas")
        layout.addWidget(canvas)

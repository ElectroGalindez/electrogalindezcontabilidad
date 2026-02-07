from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QFormLayout,
)

from backend.usuarios import login


class LoginTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.usuario_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        form.addRow(QLabel("Usuario"), self.usuario_input)
        form.addRow(QLabel("Contraseña"), self.password_input)
        layout.addLayout(form)

        self.login_button = QPushButton("Iniciar sesión")
        self.login_button.clicked.connect(self._handle_login)
        layout.addWidget(self.login_button)

    def _handle_login(self) -> None:
        usuario = self.usuario_input.text().strip()
        password = self.password_input.text()

        try:
            resultado = login(usuario, password)
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))
            return

        if resultado:
            QMessageBox.information(self, "Éxito", "Inicio de sesión correcto.")
        else:
            QMessageBox.warning(self, "Error", "Usuario o contraseña incorrectos.")

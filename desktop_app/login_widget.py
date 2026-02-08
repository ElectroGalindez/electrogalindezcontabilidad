from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class LoginWidget(QWidget):
    """Widget de login para la aplicación de escritorio."""

    def __init__(
        self,
        on_login_success: Callable[[dict], None],
        max_attempts: int = 3,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.on_login_success = on_login_success
        self.max_attempts = max_attempts
        self.failed_attempts = 0

        self.setWindowTitle("ElectroGalíndez | Login")
        self.setMinimumWidth(360)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Usuario")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.setEchoMode(QLineEdit.Password)

        self.role_label = QLabel("Rol: -")
        self.role_label.setAlignment(Qt.AlignLeft)

        self.login_button = QPushButton("Ingresar")
        self.login_button.clicked.connect(self.handle_login)

        self.lock_label = QLabel("")
        self.lock_label.setStyleSheet("color: #a00;")

        form_layout = QFormLayout()
        form_layout.addRow("Usuario:", self.username_input)
        form_layout.addRow("Contraseña:", self.password_input)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.login_button)

        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(self.role_label)
        layout.addWidget(self.lock_label)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def handle_login(self) -> None:
        if self.failed_attempts >= self.max_attempts:
            QMessageBox.warning(self, "Bloqueado", "Has excedido el número de intentos.")
            return

        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Datos incompletos", "Ingresa usuario y contraseña.")
            return

        user = self.authenticate(username, password)
        if user:
            self.role_label.setText(f"Rol: {user.get('rol', '-')}")
            QMessageBox.information(self, "Bienvenido", f"Hola {user.get('nombre', username)}")
            self.on_login_success(user)
            return

        self.failed_attempts += 1
        remaining = self.max_attempts - self.failed_attempts
        self.lock_label.setText(f"Intentos restantes: {remaining}")
        QMessageBox.critical(self, "Error", "Credenciales inválidas.")

        if self.failed_attempts >= self.max_attempts:
            self.login_button.setEnabled(False)
            self.lock_label.setText("Login bloqueado. Contacta al administrador.")

    def authenticate(self, username: str, password: str) -> Optional[dict]:
        """Conectar aquí el backend de autenticación."""
        return None

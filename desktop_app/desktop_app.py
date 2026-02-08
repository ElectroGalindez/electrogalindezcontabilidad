import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from .login_widget import LoginWidget
from .main_window import MainWindow


def run_app() -> None:
    app = QApplication(sys.argv)

    def handle_login_success(user: dict) -> None:
        main_window = MainWindow(current_user=user)
        main_window.show()
        login_widget.close()

    login_widget = LoginWidget(on_login_success=handle_login_success)
    login_widget.show()

    if not login_widget.isVisible():
        QMessageBox.critical(None, "Error", "No se pudo iniciar la ventana de login.")
        sys.exit(1)

    sys.exit(app.exec())


if __name__ == "__main__":
    run_app()

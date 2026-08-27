import sys

from PyQt6.QtWidgets import QApplication

from ame.gui.window import MainWindow


def main_app() -> None:
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

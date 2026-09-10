from typing import final

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QWidget,
)

from modules.gui.main.chat_panel import ChatPanel
from modules.gui.main.left_panel import LeftPanel


@final
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My App")
        self.resize(1200, 900)

        center_widget = QWidget()
        hbox_layout = QHBoxLayout()
        hbox_layout.setContentsMargins(0, 0, 0, 0)
        hbox_layout.setSpacing(0)

        self.left_panel = LeftPanel()
        self.chat_panel = ChatPanel()

        hbox_layout.addWidget(self.left_panel)
        hbox_layout.addWidget(self.chat_panel, stretch=1)

        center_widget.setLayout(hbox_layout)
        self.setCentralWidget(center_widget)
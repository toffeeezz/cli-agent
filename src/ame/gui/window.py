import datetime
from typing import final
from zoneinfo import ZoneInfo

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QPainterPath, QRegion, QResizeEvent
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ame.gui.components.chat import Message


class _RoundedTextEdit(QTextEdit):
    """QTextEdit with a viewport that actually respects border-radius clipping."""

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 12, 12)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))


@final
class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("GUI")
        self.setMinimumSize(900, 800)

        self.main_widget = QWidget()
        self.main_widget.setStyleSheet("QWidget { background-color: #201933; }")
        self.main_layout = QHBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.sidebar_widget = QWidget()
        self.sidebar_widget.setFixedWidth(200)
        self.sidebar_widget.setStyleSheet("QWidget { background-color: #32304A; }")
        sidebar_layout = QVBoxLayout(self.sidebar_widget)
        sidebar_layout.addWidget(QPushButton("Option 1"))
        sidebar_layout.addWidget(QPushButton("Option 2"))

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)

        self.chat_scroll_area = QScrollArea()
        self.chat_scroll_area.setWidgetResizable(True)
        self.chat_scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )

        chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(chat_widget)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.addStretch()

        # ---------------------------------------------------------------
        # INPUT BAR
        # ---------------------------------------------------------------
        input_widget = QWidget()
        input_widget.setFixedHeight(100)
        input_widget.setStyleSheet("""
            QWidget {
                background-color: #2A2340;
                border-radius: 16px;
            }
        """)
        input_layout = QHBoxLayout(input_widget)
        input_layout.setContentsMargins(12, 12, 12, 12)
        input_layout.setSpacing(10)

        self.input_field = _RoundedTextEdit()
        self.input_field.setPlaceholderText("Message Ame-chan...")
        self.input_field.setStyleSheet("""
            QTextEdit {
                background-color: #403366;
                color: #EAE3EF;
                border: 2px solid #4A4650;
                border-radius: 12px;
                padding: 10px;
                font-size: 14px;
                selection-background-color: #574D72;
            }
            QTextEdit:focus {
                border: 2px solid #CDC0EC;
            }
        """)

        self.send_button = QPushButton("Send")
        self.send_button.setFixedSize(70, 40)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #574D72;
                color: #E9DEFF;
                border-radius: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #6B5D8C;
            }
            QPushButton:pressed {
                background-color: #473A6A;
            }
        """)
        self.send_button.clicked.connect(
            lambda: (
                self.add_chat_bubble(self.input_field.toPlainText(), from_user=True),
                self.input_field.clear(),
            )
        )

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button, 0, Qt.AlignmentFlag.AlignBottom)

        content_layout.addWidget(self.chat_scroll_area)
        content_layout.addWidget(input_widget)

        self.main_layout.addWidget(self.sidebar_widget)
        self.main_layout.addWidget(content_widget)
        self.setCentralWidget(self.main_widget)

        self.chat_scroll_area.setWidget(chat_widget)

    def add_chat_bubble(self, message: str, from_user: bool) -> None:
        now = datetime.datetime.now(ZoneInfo("Asia/Manila"))
        time = now.strftime("%H:%M %p")
        self.chat_layout.addWidget(Message(message, from_user, time))

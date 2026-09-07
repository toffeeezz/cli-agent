from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class ChatPanel(QWidget):
    """Right-side panel: chat messages + text input."""

    def __init__(self):
        super().__init__()
        self.setObjectName("chatPanel")
        self.setStyleSheet("background-color: #FDE9F0")
        self.setAutoFillBackground(True)

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # --- Header ---
        header_label = QLabel("Chat")
        header_label.setObjectName("chatHeader")
        header_label.setStyleSheet("font-size: 16px; font-weight: 700;")
        layout.addWidget(header_label)

        # --- Scrollable message area ---
        self.message_container = QWidget()
        self.message_container.setObjectName("messageContainer")
        self.message_container.setStyleSheet("background: transparent;")

        self.message_layout = QVBoxLayout()
        self.message_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.message_layout.setSpacing(6)
        self.message_layout.setContentsMargins(0, 0, 0, 0)
        self.message_container.setLayout(self.message_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("chatScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.message_container)
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        layout.addWidget(self.scroll_area, stretch=1)

        # --- Placeholder message ---
        placeholder = QLabel("Messages will appear here...")
        placeholder.setObjectName("chatPlaceholder")
        placeholder.setStyleSheet("color: #B591A3; font-style: italic;")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_layout.addWidget(placeholder)

        # --- Input area ---
        input_layout = QHBoxLayout()
        input_layout.setSpacing(6)
        input_layout.setContentsMargins(0, 4, 0, 0)

        self.message_input = QLineEdit()
        self.message_input.setObjectName("messageInput")
        self.message_input.setPlaceholderText("Type a message...")
        self.message_input.returnPressed.connect(self._send_message)

        self.send_button = QPushButton("Send")
        self.send_button.setObjectName("sendButton")
        self.send_button.clicked.connect(self._send_message)

        input_layout.addWidget(self.message_input, stretch=1)
        input_layout.addWidget(self.send_button)

        layout.addLayout(input_layout)

        self.setLayout(layout)

    def _send_message(self) -> None:
        text = self.message_input.text().strip()
        if not text:
            return

        self._add_message(text, is_user=True)
        self.message_input.clear()

        # Remove placeholder if it's the first message
        first_item = self.message_layout.itemAt(0)
        if first_item is not None:
            w = first_item.widget()
            if w and w.objectName() == "chatPlaceholder":
                w.deleteLater()

    def _add_message(self, text: str, is_user: bool = False) -> None:
        bubble = QLabel(text)
        bubble.setObjectName("userMessage" if is_user else "botMessage")
        bubble.setWordWrap(True)
        bubble.setStyleSheet(
            "background-color: #FF5C9E; color: #FFF5F8;"
            " border-radius: 8px; padding: 8px 12px;"
            if is_user
            else "background-color: #FFD6E8; color: #3A1729;"
            " border-radius: 8px; padding: 8px 12px;"
        )
        bubble.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum
        )
        self.message_layout.addWidget(bubble)

        # Scroll to bottom
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
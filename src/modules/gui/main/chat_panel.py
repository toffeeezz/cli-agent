import logging
import math
import re
from typing import final, override

import markdown
from pygments.formatters import HtmlFormatter
from PyQt6.QtCore import QEvent, QObject, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QKeyEvent, QTextCursor, QTextDocument
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


@final
class ChatPanel(QWidget):
    """Right-side panel: chat messages + text input."""

    user_msg_sent: pyqtSignal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("chatPanel")

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
        self.message_layout.setContentsMargins(15, 0, 15, 0)
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

        self.message_input = QTextEdit()
        self.message_input.setObjectName("messageInput")
        self.message_input.setPlaceholderText(
            "Type a message... (Shift+Enter for new line)"
        )
        self.message_input.setFixedHeight(60)
        self.message_input.setAcceptRichText(False)
        self.message_input.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.message_input.installEventFilter(self)

        self.send_button = QPushButton("Send")
        self.send_button.setObjectName("sendButton")
        self.send_button.clicked.connect(self._send_message)

        input_layout.addWidget(self.message_input, stretch=1)
        input_layout.addWidget(self.send_button)

        layout.addLayout(input_layout)

        self.setLayout(layout)

    @override
    def eventFilter(self, a0: QObject | None, a1: QEvent | None) -> bool:
        if (
            a0 == self.message_input
            and isinstance(a1, QKeyEvent)
            and a1.type() == QEvent.Type.KeyPress
            and a1.key() == Qt.Key.Key_Return
            and not (a1.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        ):
            self._send_message()
            return True
        return super().eventFilter(a0, a1)

    def _send_message(self) -> None:
        text = self.message_input.toPlainText().strip()
        if not text:
            return

        self.add_message(text, is_user=True)
        self.message_input.clear()

        self.user_msg_sent.emit(text)

    # [ame] refactored: build rendered HTML first, pass it to both probe and bubble,
    #                 moved ensurePolished after setHtml, fixed _measure_natural_width
    # [ame] fixed auto-scroll: defer scroll so layout has time to include new bubble
    def add_message(self, text: str, is_user: bool = False) -> None:

        first_item = self.message_layout.itemAt(0)
        if first_item is not None:
            w = first_item.widget()
            if w and w.objectName() == "chatPlaceholder":
                w.deleteLater()

        bubble = QTextBrowser()
        bubble.setObjectName("userMessage" if is_user else "botMessage")
        bubble.setOpenExternalLinks(True)
        bubble.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        bubble.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        bubble.setFrameStyle(QFrame.Shape.NoFrame)

        document = bubble.document()
        viewport = self.scroll_area.viewport()

        if document is None:
            logger.error("The QTextDocument is None")
            return
        if viewport is None:
            logger.error("The Viewport is None")
            return

        document.setDocumentMargin(0)
        document.setDefaultFont(bubble.font())

        CODE_BLOCK_CSS = HtmlFormatter(style="emacs").get_style_defs(".codehilite")

        GLOBAL_STYLE = f"""
        QScrollArea {{
            background-color: #1e1e1e;
            border: none;
        }}
        QWidget#chatContainer {{
            background-color: #1e1e1e;
        }}
        QTextBrowser {{
            background-color: #2d2d2d;
            color: #ffffff;
            border-radius: 10px;
            padding: 10px;
            border: none;
        }}
        /* Inject Pygments syntax highlighting styles */
        {CODE_BLOCK_CSS}
        /* Style the overall <pre> container for the markdown code blocks */
        .codehilite {{
            background-color: #1a1a1a;
            border-radius: 6px;
            padding: 8px;
            display: block;
        }}
        .codehilite pre {{
            color: #f8f8f2;
            padding: 8px;
            border-radius: 5px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 13px;
            overflow-x: auto;
        }}
        """

        # Style
        if is_user:
            bubble.setStyleSheet(
                """
                background-color: #FF5C9E; color: #FFF5F8;
                border-radius: 8px; padding: 8px 15px;
                """
            )
        else:
            bubble.setStyleSheet(
                """
                background-color: #FFD6E8; color: #3A1729;
                border-radius: 8px; padding: 8px 15px;
                """
            )

        # Build rendered HTML first so we can measure it properly
        html_content = markdown.markdown(text, extensions=["fenced_code", "codehilite"])
        html_content = re.sub(
            r'(<div class="codehilite">.*?</div>)',
            r'<table cellpadding="8" cellspacing="0" width="100%" '
            + r'style="background-color:#1a1a1a; border-radius:12px;">'
            + r"<tr><td>\1</td></tr></table>",
            html_content,
            flags=re.DOTALL,
        )

        document.setDefaultStyleSheet(GLOBAL_STYLE)
        bubble.setHtml(f"<html><body>{html_content}</body></html>")
        bubble.ensurePolished()

        cursor = bubble.textCursor()
        _ = cursor.movePosition(QTextCursor.MoveOperation.Start)
        bubble.setTextCursor(cursor)

        horizontal_padding = 30
        vertical_padding = 16

        max_content_width = int(viewport.width() * 0.7) - horizontal_padding
        natural_width = self._measure_natural_width(
            html_content, bubble.font(), GLOBAL_STYLE
        )
        content_width = min(natural_width, max_content_width)

        document.setTextWidth(content_width)
        content_height = int(document.size().height()) + 30

        bubble.setFixedWidth(content_width + horizontal_padding)
        bubble.setFixedHeight(content_height + vertical_padding)
        bubble.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.message_layout.addWidget(bubble)

        # [ame] defer scroll so layout recalculates with the new bubble first
        QTimer.singleShot(0, self._scroll_to_bottom)

    def _scroll_to_bottom(self) -> None:
        scrollbar = self.scroll_area.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())

    def _measure_natural_width(
        self, html_content: str, reference_font: QFont, style_sheet: str
    ) -> int:
        probe = QTextDocument()
        probe.setDocumentMargin(0)
        probe.setDefaultFont(reference_font)
        probe.setDefaultStyleSheet(style_sheet)
        probe.setHtml(f"<html><body>{html_content}</body></html>")
        probe.setTextWidth(-1)
        return math.ceil(probe.idealWidth()) + 2
import logging
import math
import re
from typing import final, override

import markdown
from pygments.formatters import HtmlFormatter
from PyQt6.QtCore import QEvent, QObject, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QKeyEvent, QPixmap, QTextCursor, QTextDocument
from PyQt6.QtWidgets import (
    QFileDialog,
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

from modules.utils.qt_helper import scale_pixmap

logger = logging.getLogger(__name__)


@final
class ChatPanel(QWidget):
    """Right-side panel: chat messages + text input."""

    # [ame] updated: signal now carries images too — list[str]
    user_msg_sent: pyqtSignal = pyqtSignal(str, list)

    def __init__(self):
        super().__init__()
        self.setObjectName("chatPanel")

        # [ame] image paths waiting to be sent with the next message
        self.pending_images: list[str] = []

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

        # --- Attachment preview strip (hidden until something is pending) ---
        # [ame] added: dedicated row above the input so thumbnails don't fight
        #              with the message_input stretch inside the input row.
        self.attachment_preview = QWidget()
        self.attachment_preview.setObjectName("attachmentPreview")
        self.attachment_layout = QHBoxLayout()
        self.attachment_layout.setContentsMargins(0, 0, 0, 0)
        self.attachment_layout.setSpacing(6)
        self.attachment_layout.addStretch(1)
        self.attachment_preview.setLayout(self.attachment_layout)
        self.attachment_preview.setVisible(False)
        layout.addWidget(self.attachment_preview)

        # --- Input area ---
        input_layout = QHBoxLayout()
        input_layout.setSpacing(6)
        input_layout.setContentsMargins(0, 4, 0, 0)

        # [ame] added: upload button for image attachments
        self.upload_button = QPushButton("📎")
        self.upload_button.setObjectName("uploadButton")
        self.upload_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.upload_button.setToolTip("Attach image(s)")
        self.upload_button.clicked.connect(self._pick_images)

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

        input_layout.addWidget(self.upload_button)
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
        if not text and not self.pending_images:
            return

        # [ame] images and text go in as separate bubbles, image(s) first
        for path in self.pending_images:
            self.add_image_message(path)
        if text:
            self.add_message(text, is_user=True)

        # [ame] collapse pending images into the signal's union shape
        images = list(self.pending_images)

        self.pending_images.clear()
        self._refresh_attachment_preview()
        self.message_input.clear()

        self.user_msg_sent.emit(text, images)

    # [ame] added: multi-select file picker for image attachments
    def pick_images(self) -> list[str]:
        """Open a file picker for images and return the selected paths.

        Returns an empty list if the user cancels the dialog.
        """
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select image(s)",
            "",
            "Images (*.png *.jpg *.jpeg *.webp *.gif *.bmp);;All Files (*)",
        )
        return paths

    def _pick_images(self) -> None:
        paths = self.pick_images()
        if not paths:
            return
        self.pending_images.extend(paths)
        self._refresh_attachment_preview()

    # [ame] added: rebuild the preview strip from self.pending_images
    def _refresh_attachment_preview(self) -> None:
        while self.attachment_layout.count():
            item = self.attachment_layout.takeAt(0)
            if item is None:
                continue
            w = item.widget()
            if w is not None:
                w.deleteLater()

        for path in self.pending_images:
            self.attachment_layout.addWidget(self._make_thumbnail(path))
        self.attachment_layout.addStretch(1)

        self.attachment_preview.setVisible(bool(self.pending_images))

    # [ame] added: small removable thumbnail for one pending attachment
    def _make_thumbnail(self, path: str) -> QWidget:
        container = QWidget()
        container.setObjectName("attachmentThumb")
        thumb_layout = QHBoxLayout()
        thumb_layout.setContentsMargins(2, 2, 2, 2)
        thumb_layout.setSpacing(2)

        label = QLabel()
        label.setFixedSize(48, 48)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            factor = 48 / max(pixmap.width(), pixmap.height(), 1)
            label.setPixmap(scale_pixmap(pixmap, factor))

        remove_btn = QPushButton("×")
        remove_btn.setObjectName("attachmentRemove")
        remove_btn.setFixedSize(16, 16)
        remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_btn.clicked.connect(lambda _, p=path: self._remove_pending_image(p))

        thumb_layout.addWidget(label)
        thumb_layout.addWidget(remove_btn)
        container.setLayout(thumb_layout)
        return container

    def _remove_pending_image(self, path: str) -> None:
        if path in self.pending_images:
            self.pending_images.remove(path)
        self._refresh_attachment_preview()

    # [ame] added: drop the placeholder label once real content arrives
    def _remove_placeholder(self) -> None:
        first_item = self.message_layout.itemAt(0)
        if first_item is not None:
            w = first_item.widget()
            if w and w.objectName() == "chatPlaceholder":
                w.deleteLater()

    # [ame] refactored: build rendered HTML first, pass it to both probe and bubble,
    #                 moved ensurePolished after setHtml, fixed _measure_natural_width
    # [ame] fixed auto-scroll: defer scroll so layout has time to include new bubble
    def add_message(self, text: str, is_user: bool = False) -> None:

        self._remove_placeholder()

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

    # [ame] added: render an image as its own chat bubble, capped at 70% width
    def add_image_message(self, path: str) -> None:

        self._remove_placeholder()

        viewport = self.scroll_area.viewport()
        if viewport is None:
            logger.error("The Viewport is None")
            return

        pixmap = QPixmap(path)
        if pixmap.isNull():
            logger.error("Failed to load image: %s", path)
            return

        horizontal_padding = 30
        vertical_padding = 16

        max_content_width = int(viewport.width() * 0.7) - horizontal_padding
        if pixmap.width() > max_content_width:
            pixmap = scale_pixmap(pixmap, max_content_width / pixmap.width())

        bubble = QLabel()
        bubble.setObjectName("userImage")
        bubble.setPixmap(pixmap)
        bubble.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bubble.setStyleSheet(
            """
            background-color: #FF5C9E;
            border-radius: 8px;
            """
        )
        bubble.setFixedSize(
            pixmap.width() + horizontal_padding,
            pixmap.height() + vertical_padding,
        )
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


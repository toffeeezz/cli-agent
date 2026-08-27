import sys
from typing import final

import markdown
from pygments.formatters import HtmlFormatter
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QPainterPath, QRegion, QResizeEvent
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QTextBrowser,
    QTextEdit,
    QWidget,
)


class _MessageBubble(QTextBrowser):
    def __init__(self, raw_markdown: str) -> None:
        super().__init__()
        self.setOpenExternalLinks(True)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)

        self.document().setDocumentMargin(10)

        html_content = markdown.markdown(
            raw_markdown.strip(),
            extensions=["extra", "codehilite"],
            extension_configs={
                "codehilite": {
                    "css_class": "highlight",
                    "guess_lang": True,
                    "use_pygments": True,
                    "noclasses": False,
                    "linenums": False,
                }
            },
        )

        style_defs = HtmlFormatter(style="github-dark").get_style_defs(".highlight")

        full_html = f"""
        <html>
        <head>
            <style>
                body {{
                    background-color: #403366;
                    color: #CBC1E6;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    border-radius: 10px;
                }}
                {style_defs}
                pre {{
                    background-color: #30264C!important;
                    border: 5px solid #3e3e3e;
                    border-radius: 30px;
                    padding: 12px;
                    font-family: 'Consolas', 'Courier New', monospace;
                }}
                .highlight p, .highlight div, .highlight span {{
                    margin: 0 !important;
                    padding: 0;
                    background-color: transparent !important; /* Prevents line-by-line stripes */
                    border-radius: 10px;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        self.setHtml(full_html)

        self.document().contentsChanged.connect(self.adjust_height)

    def adjust_height(self) -> None:
        self.document().setTextWidth(-1)
        natural_width = int(self.document().idealWidth())
        max_allowed_width = 450
        if natural_width > max_allowed_width:
            self.document().setTextWidth(max_allowed_width)
            final_width = max_allowed_width + 20
        else:
            final_width = natural_width

        final_height = int(self.document().size().height())

        _ = self.blockSignals(True)
        self.setFixedWidth(final_width)
        self.setFixedHeight(final_height)
        _ = self.blockSignals(False)

        if self.parentWidget():
            self.parentWidget().updateGeometry()

        self._update_mask()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.adjust_height()
        self._update_mask()

    def _update_mask(self) -> None:
        path = QPainterPath()
        path.addRoundedRect(
            QRectF(self.rect()), 10, 10
        )  # match your QSS border-radius value
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)


@final
class Message(QWidget):
    def __init__(self, message: str, from_user: bool, time: str) -> None:
        super().__init__()
        self.message = message
        self.from_user = from_user

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        profile_placeholder = QLabel()
        profile_placeholder.setFixedSize(20, 20)
        profile_placeholder.setStyleSheet("""
            QLabel {
                background-color: #007ACC;
                border-radius: 10px;
                color: white;
            }
        """)

        time_label = QLabel(time)
        time_label.setStyleSheet("""
            QLabel {
                color: #C0B2E6;
            }
                                 """)

        bubble = _MessageBubble(self.message)

        if from_user:
            layout.setAlignment(Qt.AlignmentFlag.AlignRight)
            layout.addWidget(time_label, 0, Qt.AlignmentFlag.AlignBottom)
            layout.addWidget(bubble, 0, Qt.AlignmentFlag.AlignBottom)
            layout.addWidget(profile_placeholder, 0, Qt.AlignmentFlag.AlignBottom)
        else:
            layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(profile_placeholder, 0, Qt.AlignmentFlag.AlignBottom)
            layout.addWidget(bubble, 0, Qt.AlignmentFlag.AlignBottom)
            layout.addWidget(time_label, 0, Qt.AlignmentFlag.AlignBottom)

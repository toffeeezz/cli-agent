from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from modules.utils.qt_helper import scale_pixmap
from modules.utils.resource import get_resource_fullpath


class LeftPanel(QWidget):
    """Left side panel — webcam display + menu buttons."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("leftPanel")
        self.setMaximumWidth(400)

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # --- Webcam / live-stream area ---
        cam_container = QWidget()
        cam_container.setObjectName("camContainer")
        cam_container.setStyleSheet("background-color: transparent;")

        self.cam_label = QLabel()
        self.cam_label.setObjectName("camLabel")
        self.cam_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        pixmap = QPixmap(str(get_resource_fullpath("imgs/bg_stream.webp")))
        if pixmap and not pixmap.isNull():
            scaled = scale_pixmap(pixmap, 0.5)
            self.cam_label.setPixmap(scaled)
            cam_container.setMaximumSize(scaled.width(), scaled.height())
        else:
            self.cam_label.setText("📷 No Camera Feed")
            self.cam_label.setStyleSheet("color: #7A4A63; font-size: 14px;")
            cam_container.setMaximumSize(320, 240)

        cam_layout = QVBoxLayout()
        cam_layout.setContentsMargins(0, 0, 0, 0)
        cam_layout.addWidget(self.cam_label)
        cam_container.setLayout(cam_layout)

        layout.addWidget(cam_container, alignment=Qt.AlignmentFlag.AlignHCenter)

        # --- Menu buttons ---
        btn_specs = [
            ("toggleCamera", "📷  Toggle Camera"),
            ("settingsBtn",   "⚙️  Settings"),
            ("themeBtn",      "🎨  Change Theme"),
            ("aboutBtn",      "ℹ️  About"),
        ]

        for obj_name, text in btn_specs:
            btn = QPushButton(text)
            btn.setObjectName(obj_name)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(btn)

        # Spacer to push everything up
        layout.addStretch(1)

        self.setLayout(layout)
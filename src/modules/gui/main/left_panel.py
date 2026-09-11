from pathlib import Path
from typing import final

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from modules.gui.webcam_panel import Webcam
from modules.utils.qt_helper import scale_pixmap
from modules.utils.resource import get_resource_fullpath


@final
class LeftPanel(QWidget):
    """Left side panel — webcam display + menu buttons."""

    toggle_camera_clicked: pyqtSignal = pyqtSignal()
    save_session_clicked: pyqtSignal = pyqtSignal(str)
    load_session_clicked: pyqtSignal = pyqtSignal(bool, str)
    settings_clicked: pyqtSignal = pyqtSignal()
    theme_clicked: pyqtSignal = pyqtSignal()
    about_clicked: pyqtSignal = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
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
        self.cam_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(str(get_resource_fullpath("imgs/bg_stream.webp")))
        if pixmap and not pixmap.isNull():
            scaled = scale_pixmap(pixmap, 0.5)
            self.cam_label.setPixmap(scaled)
            cam_container.setMaximumSize(scaled.width(), scaled.height())
        else:
            self.cam_label.setText("📷 No Camera Feed")
            self.cam_label.setStyleSheet("color: #7A4A63; font-size: 14px;")
            cam_container.setMaximumSize(320, 240)

        self.webcam = Webcam()
        cam_layout = QGridLayout()
        cam_layout.setContentsMargins(0, 0, 0, 0)
        cam_layout.addWidget(self.cam_label, 0, 0)
        cam_layout.addWidget(self.webcam, 0, 0)
        cam_container.setLayout(cam_layout)

        layout.addWidget(cam_container, alignment=Qt.AlignmentFlag.AlignHCenter)

        # --- Menu buttons ---
        btn_specs = [
            ("toggleCamera", "📷  Toggle Camera", self.toggle_camera_clicked),
            ("saveSession", "🔽️  Save Session", self._save_session),
            ("loadSession", "▶️  Load Session", self._load_session),
            ("settingsBtn", "⚙️  Settings", self.settings_clicked),
            ("themeBtn", "🎨  Change Theme", self.theme_clicked),
            ("aboutBtn", "ℹ️  About", self.about_clicked),
        ]

        for obj_name, text, func in btn_specs:
            btn = QPushButton(text)
            btn.setObjectName(obj_name)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(func)
            layout.addWidget(btn)

        layout.addStretch(1)

        self.setLayout(layout)

    def _load_session(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            None, "Save session as", "", "JSON Files (*.json)"
        )
        if not path:
            return
        if not Path(path).exists():
            _ = QMessageBox.warning(
                self, "File does not exist", "The selected file does not exist"
            )
            self.load_session_clicked.emit(False, "Selected file does not exist")
        if not path.endswith(".json"):
            _ = QMessageBox.warning(
                self,
                "Invalid file format",
                "The selected file is not a valid json file",
            )
            self.load_session_clicked.emit(False, "Selected file is not a json format")
        self.load_session_clicked.emit(True, path)

    def _save_session(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            None, "Save session as", "session.json", "JSON Files (*.json)"
        )
        if not path:
            return
        if not path.endswith(".json"):
            path += ".json"
        self.save_session_clicked.emit(path)

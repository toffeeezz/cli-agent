from pathlib import Path
from typing import final

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from dotenv import set_key

from modules.config.models import Config
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
    config_changed: pyqtSignal = pyqtSignal()

    def __init__(self, config: Config | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("leftPanel")
        self.setMaximumWidth(400)

        self.config = config or Config()

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
            ("settingsBtn", "⚙️  Settings", self._show_settings),  # [ame] wired to popup
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

    # [ame] settings popup — reads/writes self.config directly
    def _show_settings(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Settings")
        dialog.setMinimumWidth(400)

        main_layout = QVBoxLayout(dialog)

        form_layout = QFormLayout()
        form_layout.setSpacing(8)

        model_combo = QComboBox()
        model_combo.addItems(
            [
                "deepseek/deepseek-v4-flash",
                "deepseek/deepseek-v4.1-flash",
            ]
        )
        model_combo.setCurrentText(self.config.agent.model)
        form_layout.addRow("Model:", model_combo)

        backend_combo = QComboBox()
        backend_combo.addItems(["proxy", "koboldcpp"])
        backend_combo.setCurrentText(self.config.agent.backend)
        form_layout.addRow("Backend:", backend_combo)

        temp_float = QDoubleSpinBox()
        temp_float.setRange(0.0, 2.0)
        temp_float.setSingleStep(0.1)
        temp_float.setValue(self.config.agent.temperature)
        form_layout.addRow("Temperature:", temp_float)

        api_key_input = QLineEdit()
        api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        api_key_input.setText(self.config.agent.api_key)
        form_layout.addRow("API Key:", api_key_input)

        # --- UI section ---
        theme_combo = QComboBox()
        theme_combo.addItems(["default", "dark", "light"])
        theme_combo.setCurrentText(self.config.gui.theme)
        form_layout.addRow("Theme:", theme_combo)

        camera_check = QCheckBox("Enable camera on startup")
        camera_check.setChecked(self.config.gui.camera_enabled_on_start)
        form_layout.addRow("", camera_check)

        loop_spin = QSpinBox()
        loop_spin.setRange(1, 200)
        loop_spin.setValue(self.config.agent.max_loops)
        form_layout.addRow("Max Loops:", loop_spin)

        main_layout.addLayout(form_layout)

        # --- Buttons ---
        btn_layout = QHBoxLayout()

        def save():
            self.config.agent.model = model_combo.currentText()
            self.config.agent.backend = backend_combo.currentText()
            self.config.agent.temperature = temp_float.value()
            self.config.agent.api_key = api_key_input.text()
            self.config.gui.theme = theme_combo.currentText()
            self.config.gui.camera_enabled_on_start = camera_check.isChecked()
            self.config.agent.max_loops = loop_spin.value()
            _ = set_key("../../../.env", "api_key", self.config.agent.api_key)
            self.config_changed.emit()
            dialog.accept()

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)

        main_layout.addLayout(btn_layout)

        _ = dialog.exec()

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

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLayout


def scale_pixmap(pixmap: QPixmap, factor: float) -> QPixmap:
    return pixmap.scaled(
        int(pixmap.width() * factor),
        int(pixmap.height() * factor),
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


def clear_layout(layout: QLayout):
    item = layout.takeAt(0)
    if not item:
        return
    widget = item.widget()
    if not widget:
        return
    while layout.count():
        widget.deleteLater()  # Safely deletes the widget

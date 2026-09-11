from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap


def scale_pixmap(pixmap: QPixmap, factor: float) -> QPixmap:
    return pixmap.scaled(
        int(pixmap.width() * factor),
        int(pixmap.height() * factor),
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )

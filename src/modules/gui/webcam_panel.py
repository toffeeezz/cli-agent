from enum import Enum
from typing import final

from PyQt6.QtGui import QMovie
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from modules.utils.resource import get_resource_fullpath


class State(Enum):
    IDLE = 0
    TYPING = 1


@final
class Webcam(QWidget):
    background: str = ""
    ame_gif: QMovie
    movie_label: QLabel
    ame_state: State = State.IDLE
    _ame_gifs: dict[State, str]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._ame_gifs = {
            State.IDLE: str(get_resource_fullpath("imgs/ame-sleepy.webp")) or "",
            State.TYPING: str(get_resource_fullpath("imgs/ame-texting.webp")) or "",
        }
        self.ame_gif = QMovie(self._ame_gifs[State.IDLE])
        self.ame_gif.start()

        self.movie_label = QLabel()
        self.movie_label.setMovie(self.ame_gif)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(self.movie_label)

        self.setLayout(layout)

    def change_state(self, state: State) -> None:
        self.ame_gif.stop()
        self.ame_state = state
        gif = self._get_current_gif()
        self.ame_gif.setFileName(gif)
        self.ame_gif.start()
        self.movie_label.setMovie(self.ame_gif)

    def _get_current_gif(self) -> str:
        return self._ame_gifs[self.ame_state]

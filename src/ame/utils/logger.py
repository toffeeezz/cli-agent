import logging
from typing import Literal

from rich.logging import RichHandler

from ame.cli.renderer import console

root = logging.getLogger()
console_handler = RichHandler(
    console=console, rich_tracebacks=True, markup=True, show_path=False
)
file_handler = logging.FileHandler("ame.log")

DEFAULT_CONSOLE_LEVEL = logging.CRITICAL + 1  # silent by default


def setup_logging() -> None:
    root.setLevel(logging.DEBUG)
    console_handler.setLevel(DEFAULT_CONSOLE_LEVEL)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("[%(levelname)s] (%(asctime)s) - %(name)s -  - %(message)s")
    )
    if console_handler not in root.handlers:
        root.addHandler(console_handler)
    if file_handler not in root.handlers:
        root.addHandler(file_handler)


def set_console_level(level: Literal["warning", "none", "info", "debug"]) -> None:
    match level:
        case "info":
            console_handler.setLevel(logging.INFO)
        case "debug":
            console_handler.setLevel(logging.DEBUG)
        case "warning":
            console_handler.setLevel(logging.WARNING)
        case "none":
            console_handler.setLevel(logging.CRITICAL + 1)

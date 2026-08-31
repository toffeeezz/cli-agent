from pathlib import Path

from pydantic import ValidationError

from modules.cli.renderer import console
from modules.config.models import Config

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config.json"


def load_config() -> tuple[bool, Config | None]:
    try:
        with open(CONFIG_PATH, "r") as file:
            config = Config.model_validate_json(file.read())
        return True, config
    except FileNotFoundError:
        console.print(
            "[yellow]WARNING:[/] Missing config settings!! Generating from scratch..."
        )
        with open(CONFIG_PATH, "w", encoding="utf-8") as file:
            config = Config()
            _ = file.write(config.model_dump_json(indent=4))
        return True, None
    except ValidationError as e:
        console.print(
            "[red]ERROR: Failed to load config settings due to improper formatting or syntax errors"
        )
        console.print(f"[yellow]{e}")
        return False, None

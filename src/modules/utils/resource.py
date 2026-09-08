from pathlib import Path

_RESOURCE_DIR: Path = Path(__file__).resolve().parent.parent.parent / "res"


def get_resource_fullpath(relative_path: str) -> Path | None:
    target = _RESOURCE_DIR / relative_path
    if not target.exists():
        return None

    return target

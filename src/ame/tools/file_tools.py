import logging
from pathlib import Path

import send2trash

from ame.tools.tool_registry import tool_registry

# NOTE: No path sandboxing — intentional for personal/local use only.
# Do not reuse this code as-is in any multi-user or exposed context.

logger = logging.getLogger(__name__)


@tool_registry.register()
def read_file(path: str) -> tuple[bool, str]:
    """Reads and returns the full text contents of a file at the given path.

    Use this to inspect a file's contents before editing, summarizing, or
    answering questions about what it contains. Echo it back to the user if they ask what's in it. Fails if the file does not
    exist or cannot be read due to permissions.
    """
    try:
        target = Path(path)
        content = target.read_text(encoding="utf-8")
        return True, f"The content of the file is: {content}"
    except FileNotFoundError:
        return False, "File does not exist"
    except PermissionError:
        return False, "Permission not allowed"
    except IsADirectoryError:
        return False, f"'{path}' is a directory, not a file"
    except UnicodeDecodeError:
        return False, "File is not valid UTF-8 text (likely a binary file)"


# WARNING: This overwrites existing file.
# Use append_file instead for writing existing files
@tool_registry.register()
def write_file(path: str, content: str) -> tuple[bool, str]:
    """Creates a new file or completely overwrites an existing file with the given content.

    Any existing content at this path will be permanently replaced. Use
    append_file instead if you want to add to an existing file without
    erasing what's already there.
    """
    try:
        target = Path(path)
        lines = content.splitlines(keepends=True)
        with open(target, "w", encoding="utf-8") as file:
            file.writelines(lines)
        return True, "File Written Successfully"
    except PermissionError:
        return False, "Permission not allowed"
    except FileNotFoundError:
        return False, "Parent directory does not exist"
    except IsADirectoryError:
        return False, f"'{path}' is a directory, not a file"


@tool_registry.register()
def append_file(path: str, content: str) -> tuple[bool, str]:
    """Appends content to the end of an existing file without modifying what's already there.

    The target file must already exist — use write_file to create a new file
    first if it doesn't.
    """
    target = Path(path)
    if not target.exists():
        return False, "File does not exist"
    try:
        lines = content.splitlines(keepends=True)
        with open(target, "a", encoding="utf-8") as file:
            file.writelines(lines)
        return True, "Lines appended successfully"
    except FileNotFoundError:
        return False, "File does not exist"
    except PermissionError:
        return False, "Permission not allowed"
    except IsADirectoryError:
        return False, f"'{path}' is a directory, not a file"


@tool_registry.register()
def make_dir(path: str, parents: bool = True) -> tuple[bool, str]:
    """Creates a new directory at the given path.

    If parents is True (default), any missing parent directories are created
    automatically. Succeeds silently if the directory already exists.
    """
    try:
        Path(path).mkdir(parents=parents, exist_ok=True)
        return True, "Directory successfully created"
    except PermissionError:
        return False, "Permission not allowed"
    except FileNotFoundError:
        return False, "Parent directory does not exist and parents=False"
    except NotADirectoryError:
        return False, f"A component of '{path}' is a file, not a directory"


@tool_registry.register()
def list_dir(starting_path: str) -> tuple[bool, str]:
    """Lists the contents of a directory, showing each entry's name, type, and size.

    Use this to explore a directory's structure before deciding which files
    to read, write, or delete.
    """
    try:
        entries: list[str] = []
        for entry in Path(starting_path).iterdir():
            name = entry.name
            kind = "dir" if entry.is_dir() else "file"
            size = entry.stat().st_size if entry.is_file() else "-"
            entry_str = f"Name: {name} Type: {kind} Size: {size}"
            entries.append(entry_str)
        return True, str(entries) if entries else "Directory is empty"
    except FileNotFoundError:
        return False, "Path does not exist"
    except PermissionError:
        return False, "Permission not allowed"
    except NotADirectoryError:
        return False, f"'{starting_path}' is a file, not a directory"


@tool_registry.register()
def delete_file_or_dir(path: str, confirm: bool | None = None) -> tuple[bool, str]:
    """Moves a file or directory to the trash (recoverable, not permanent deletion).

    This is destructive and requires explicit user confirmation. Call this
    tool first with confirm left unset to check what's being deleted; only
    pass confirm=True after the user has explicitly agreed, or confirm=False
    if they decline.
    """
    target = Path(path)
    if not target.exists():
        return False, f"'{path}' does not exist, nothing else to delete"
    is_dir = target.is_dir()
    if confirm is None:
        return (
            False,
            f"The provided path is a {'directory' if is_dir else 'file'}, use the approriate tool first to confirm what are its contents!!. Then ask the user for confirmation.",
        )
    if not confirm:
        return False, "The user denied the request for deletion"
    try:
        send2trash.send2trash(path)
    except OSError as e:
        return False, f"Failed to move '{path}' to trash: {e}"
    logger.warning("[bold yellow]DESTRUCTIVE ACTION: deleted '%s'", path)
    return True, f"{path} was thrown into recycle bin"

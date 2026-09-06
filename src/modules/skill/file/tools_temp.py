from pathlib import Path

from send2trash import send2trash


def validate_path(target: str) -> tuple[bool, str]:
    """Resolves the path which acts as a guardrail to prevent unauthorized access.

    Returns a tuple of (success, message) where:
    - (True, resolved_path_str) on success
    - (False, denial_message) on failure (escape attempt)
    """
    root_dir_path = Path.cwd().resolve()
    target_path = (root_dir_path / target.lstrip("/\\")).resolve()

    if not target_path.is_relative_to(root_dir_path):
        return (
            False,
            f"Access denied: '{target_path}' attempts to escape working directory.",
        )

    return True, str(target_path)


def read_file(path: str) -> tuple[bool, str]:
    """Reads and returns the full text contents of a file at the given path.

    Use this to inspect a file's contents before editing, summarizing, or
    answering questions about what it contains. Echo it back to the user if they ask what's in it. Fails if the file does not
    exist or cannot be read due to permissions.
    """
    try:
        success, target_str = validate_path(path)
        if not success:
            return False, target_str
        target = Path(target_str)
        if target.name.startswith(".") or target.suffix == ".env":
            return (
                False,
                f"Trying to access confidential files. Access denied to the target path: {target.relative_to(Path.cwd())}",
            )
        content = target.read_text(encoding="utf-8")
        return True, f"The content of the file is: {content}"
    except FileNotFoundError:
        return False, "File does not exist"
    except PermissionError:
        return False, f"Permission not allowed trying to access '{path}'"
    except IsADirectoryError:
        return False, f"'{path}' is a directory, not a file"
    except UnicodeDecodeError:
        return False, "File is not valid UTF-8 text (likely a binary file)"


# WARNING: This overwrites existing file.
# Use append_file instead for writing existing files
def write_file(path: str, content: str) -> tuple[bool, str]:
    """Creates a new file or completely overwrites an existing file with the given content.

    Any existing content at this path will be permanently replaced. Use
    append_file instead if you want to add to an existing file without
    erasing what's already there.
    """
    try:
        success, target_str = validate_path(path)
        if not success:
            return False, target_str
        target = Path(target_str)
        lines = content.splitlines(keepends=True)
        with open(target, "w", encoding="utf-8") as file:
            file.writelines(lines)
        return True, "File Written Successfully"
    except PermissionError:
        return False, f"Permission not allowed trying to access '{path}'"
    except FileNotFoundError:
        return False, "Parent directory does not exist"
    except IsADirectoryError:
        return False, f"'{path}' is a directory, not a file"


def append_file(path: str, content: str) -> tuple[bool, str]:
    """Appends content to the end of an existing file without modifying what's already there.

    The target file must already exist — use write_file to create a new file
    first if it doesn't.
    """
    success, target_str = validate_path(path)
    if not success:
        return False, target_str
    target = Path(target_str)
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
        return False, f"Permission not allowed trying to access '{path}'"
    except IsADirectoryError:
        return False, f"'{path}' is a directory, not a file"


def make_dir(path: str, parents: bool = True) -> tuple[bool, str]:
    """Creates a new directory at the given path.

    If parents is True (default), any missing parent directories are created
    automatically. Succeeds silently if the directory already exists.
    """
    try:
        success, target_str = validate_path(path)
        if not success:
            return False, target_str
        Path(target_str).mkdir(parents=parents, exist_ok=True)
        return True, "Directory successfully created"
    except PermissionError:
        return False, f"Permission not allowed trying to access '{path}'"
    except FileNotFoundError:
        return False, "Parent directory does not exist and parents=False"
    except NotADirectoryError:
        return False, f"A component of '{path}' is a file, not a directory"


def list_dir(starting_path: str) -> tuple[bool, str]:
    """Lists the contents of a directory, showing each entry's name, type, and size.

    Use this to explore a directory's structure before deciding which files
    to read, write, or delete.
    """
    try:
        success, target_str = validate_path(starting_path)
        if not success:
            return False, target_str
        entries: list[str] = []
        for entry in Path(target_str).iterdir():
            name = entry.name
            kind = "dir" if entry.is_dir() else "file"
            size = entry.stat().st_size if entry.is_file() else "-"
            entry_str = f"Name: {name} Type: {kind} Size: {size}"
            entries.append(entry_str)
        return True, str(entries) if entries else "Directory is empty"
    except FileNotFoundError:
        return False, "Path does not exist"
    except PermissionError:
        return False, f"Permission not allowed trying to access '{starting_path}'"
    except NotADirectoryError:
        return False, f"'{starting_path}' is a file, not a directory"


def delete_file_or_dir(path: str, confirm: bool | None = None) -> tuple[bool, str]:
    """Moves a file or directory to the trash (recoverable, not permanent deletion).

    This is destructive and requires explicit user confirmation. Call this
    tool first with confirm left unset to check what's being deleted; only
    pass confirm=True after the user has explicitly agreed, or confirm=False
    if they decline.
    """
    success, target_str = validate_path(path)
    if not success:
        return False, target_str
    target = Path(target_str)
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
        send2trash(path)
    except OSError as e:
        return False, f"Failed to move '{path}' to trash: {e}"
    return True, f"{path} was thrown into recycle bin"
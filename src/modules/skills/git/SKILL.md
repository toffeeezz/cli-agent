---
name: git_operations
desc: >-
  Provides secure file and directory management including reading, writing, 
  appending, listing, and safe deletion with mandatory path sandboxing.
  Triggers: "read file", "write file", "list directory", "delete file", "create folder", "append log".
  Do NOT use for git version control, remote file transfers, or parsing binary databases.
version: 1.0.0
tools:
  - read_file
  - write_file
  - append_file
  - make_dir
  - list_dir
  - delete_file_or_dir
---

## Description

A collection of utility functions designed for file and directory management. All operations include strict path sandboxing (`validate_path`) to enforce working directory limits and prevent directory traversal vulnerabilities.

---

## Tool API Reference

### 1. `read_file`
Reads and returns the full UTF-8 text contents of a file at the specified path.

* **Parameters:**
  * `path` (`str`): Target path relative to or within the current working directory.
* **Returns:** `tuple[bool, str]` — `(True, content_string)` on success, or `(False, error_message)` on failure.

---

### 2. `write_file`
Creates a new file or completely overwrites an existijkkng file with the provided string.

* **Parameters:**
  * `path` (`str`): Target file path.
  * `content` (`str`): Text content to write.
* **Returns:** `tuple[bool, str]` — `(True, "File Written Successfully")` on success, or `(False, error_message)` on failure.
* **Warning:** Overwrites existing contents permanently. Use `append_file` to preserve existing content.

---

### 3. `append_file`
Appends content to the end of an existing file.

* **Parameters:**
  * `path` (`str`): Target file path. Must exist prior to execution.
  * `content` (`str`): Text content to append.
* **Returns:** `tuple[bool, str]` — `(True, "Lines appended successfully")` on success, or `(False, error_message)` on failure.

---

### 4. `make_dir`
Creates a new directory at the specified path.

* **Parameters:**
  * `path` (`str`): Target directory path.
  * `parents` (`bool`, optional): Automatically creates missing parent directories if `True`. Defaults to `True`.
* **Returns:** `tuple[bool, str]` — `(True, "Directory successfully created")` on success, or `(False, error_message)` on failure.

---

### 5. `list_dir`
Lists directory contents, displaying name, type (`file` or `dir`), and size in bytes.

* **Parameters:**
  * `starting_path` (`str`): Path of the directory to inspect.
* **Returns:** `tuple[bool, str]` — `(True, list_representation)` on success, or `(False, error_message)` on failure.

---

### 6. `delete_file_or_dir`
Safely moves a target file or directory to the system trash using `send2trash`.

* **Parameters:**
  * `path` (`str`): Target file or directory path.
  * `confirm` (`bool | None`, optional): Confirmation flag. Defaults to `None`.
* **Returns:** `tuple[bool, str]` — `(True, success_message)` or `(False, prompt_or_error_message)`.

---

## Usage Guidelines & Safeguards

* **Path Sandboxing:** All operations enforce `validate_path()`. Attempts to escape the root directory using relative references (e.g., `../`) will trigger a `PermissionError`.
* **Deletion Protocol:**
  1. Call `delete_file_or_dir(path)` with `confirm=None` first to inspect the target type.
  2. Inspect directory contents with `list_dir()` or file contents with `read_file()` before proceeding.
  3. Prompt the user for explicit confirmation.
  4. Pass `confirm=True` only after receiving explicit user approval.
* **File Modifications:** Prefer `append_file()` when modifying logs or appending records to prevent accidental data loss from full file overwrites.

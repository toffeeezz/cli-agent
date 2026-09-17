---
name: file_system_operations
desc: >-
  Provides secure file and directory management including reading, writing, 
  appending, listing, and safe deletion with mandatory path sandboxing.
  Triggers: "read file", "write file", "list directory", "delete file", "create folder", "append log".
  Do NOT use for git version control, remote file transfers, or parsing binary databases.
tools:
  - read_file
  - write_file
  - append_file
  - make_dir
  - list_dir
  - delete_file_or_dir
  - read_document
---

## Description

A collection of utility functions designed for file and directory management. All operations include strict path sandboxing (`validate_path`) to enforce working directory limits and prevent directory traversal vulnerabilities. Parameter names/types for each tool are defined in their own docstrings — this reference covers what each tool does, what its result actually means, and how it fits into a safe workflow.

---

## Tool API Reference

### 1. `read_file`
Reads and returns the full UTF-8 text contents of a file.
* **Returns:** `(True, content_string)` on success, `(False, error_message)` on failure (e.g. file doesn't exist, not valid UTF-8, path outside sandbox).

---

### 2. `write_file`
Creates a new file or **completely overwrites** an existing one with the provided string.
* **Returns:** `(True, "File Written Successfully")` on success, `(False, error_message)` on failure.
* **Warning:** Destructive — this fully replaces existing contents with no diff or backup. There is no undo through this module. Use `append_file` instead when the goal is adding to a file rather than replacing it.

---

### 3. `append_file`
Appends content to the end of an existing file. The file must already exist.
* **Returns:** `(True, "Lines appended successfully")` on success, `(False, error_message)` on failure (e.g. file doesn't exist — this tool won't create one; use `write_file` first).

---

### 4. `make_dir`
Creates a new directory.
* **Returns:** `(True, "Directory successfully created")` on success, `(False, error_message)` on failure.

---

### 5. `list_dir`
Lists directory contents, showing name, type (`file`/`dir`), and size in bytes for each entry.
* **Returns:** `(True, list_representation)` on success, `(False, error_message)` on failure (e.g. path doesn't exist or isn't a directory).

---

### 6. `delete_file_or_dir`
Moves a file or directory to the system trash via `send2trash` (recoverable, not a permanent delete).
* **Returns:** `(True, success_message)` on success. `(False, prompt_or_error_message)` on failure or when confirmation is still pending.
* **Note:** Calling this with `confirm` unset/`None` is the intended way to "dry run" it — read the returned message, it will tell you what's about to be deleted rather than deleting it.

---

### 7. `read_document`
Extracts and returns text content from a PDF, docx file.
* **Returns:** `(True, text_content)` on success, `(False, error_message)` on failure (e.g. file isn't a valid PDF, or is a scanned/image-only PDF with no extractable text).

---

## Usage Guidelines & Safeguards

### Path Sandboxing
All operations enforce `validate_path()`. Relative traversal attempts (`../`) outside the root directory raise a `PermissionError` — if a call fails this way, don't retry with a slightly different relative path hoping it'll slip through; tell the user the path is out of bounds.

### Before writing or overwriting anything
* If `write_file` is targeting a path that might already exist and matter (not clearly a scratch/temp file), call `read_file` on it first to see what's there before you overwrite it. If it holds something non-trivial and the user didn't explicitly say "overwrite" or "replace," confirm with them before proceeding.
* If the goal is "add to" or "log" or "append" something, default to `append_file`, not `write_file`. Only use `write_file` when the intent is genuinely "replace everything" or the file is new.

### After writing or appending — always verify
Do not report a write/append as done just because the tool returned success. A success return means the syscall completed, not that the content is actually correct on disk:
1. Call `read_file` on the path immediately after `write_file` or `append_file`.
2. Compare what comes back against what you intended to write (content present, not truncated, no encoding artifacts).
3. Only then tell the user the file was written/updated. If the read-back doesn't match what you expected, say so — don't paper over a mismatch or assume it's fine.
* Skip the read-back only for trivial, low-stakes writes where the user is watching output live and would immediately notice a problem themselves (e.g. quick throwaway test files) — when in doubt, verify.

### Before creating a directory
* Consider `list_dir` on the parent path first if there's any chance the directory already exists or the parent path itself doesn't exist yet (relevant if you're calling with `parents=False`-equivalent behavior, or just want to give the user an accurate "created" vs. "already existed" answer).

### Before deleting anything
1. Call `delete_file_or_dir(path)` with `confirm` unset to find out what would be affected without committing to it.
2. Inspect the target: `list_dir()` if it's a directory (know what's inside, not just that it exists), `read_file()` if it's a file whose contents might matter.
3. Tell the user plainly what's about to be deleted, based on what you actually saw in step 2 — not a generic "deleting this file" line.
4. Only call again with `confirm=True` after the user has explicitly said yes to what you described. A vague earlier "sure, clean that up" from several turns ago doesn't count as confirmation for a specific deletion happening now — reconfirm if the request wasn't specific to this exact path.
5. After deletion, treat the success message as confirmation — don't call `list_dir` again just to double check unless the user asks, since trashing is already a soft/recoverable delete.

### General ordering logic
* Reads before writes when there's any ambiguity about existing state. Don't guess at what's in a file or directory — check.
* Don't chain multiple mutating calls (e.g. `make_dir` then `write_file` then `append_file`) without confirming each step succeeded first. If step one fails, stop — don't proceed to step two assuming it worked.
* If a call fails, read the actual error message before retrying. A sandbox violation, a missing parent directory, and a permissions error all look like "it failed" but need different fixes — don't retry blindly with the same arguments.

### Scope limits
This module handles local file/directory CRUD and PDF text extraction only. It does not handle git operations, network/remote transfers, or binary formats other than PDF (e.g. don't attempt to `read_file` a `.xlsx` or other unsupported formats and expect meaningful output — those need their own dedicated tools).

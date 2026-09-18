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

A collection of utility functions for file and directory management. All operations enforce strict path sandboxing (`validate_path`) to keep calls within the working directory and block directory traversal. Parameter names/types live in each tool's own schema — this reference covers what the schema can't: what a success/failure return actually means, and how the tools fit together safely.

---

## Tool Reference

| Tool | What it does | Return semantics / key warning |
|---|---|---|
| `read_file` | Reads full UTF-8 text of a file | Fails on non-UTF-8 content, missing file, or out-of-sandbox path. |
| `write_file` | Creates or **fully overwrites** a file | **Destructive, no undo, no diff.** Use `append_file` instead unless the intent is genuinely "replace everything." |
| `append_file` | Appends to an existing file | File must already exist — this tool never creates one; `write_file` first if it doesn't. |
| `make_dir` | Creates a directory | Fails if the parent directory doesn't exist yet — check with `list_dir` on the parent first if that's uncertain. |
| `list_dir` | Lists entries: name, type, size in bytes | Fails if the path doesn't exist or isn't a directory. |
| `delete_file_or_dir` | Moves to system trash (`send2trash`) — recoverable | Call with `confirm` unset first as a dry run; the returned message describes what *would* be deleted without committing. |
| `read_document` | Extracts text from PDF or docx | Fails on scanned/image-only PDFs with no extractable text layer, or a docx with no text runs (e.g. purely image-based content). |

---

## Usage Guidelines & Safeguards

**Path sandboxing**
`validate_path()` runs on every call. A traversal attempt (`../`) outside the root raises a `PermissionError` — if a call fails this way, don't retry with a slightly different relative path hoping it slips through. Tell the user the path is out of bounds.

**Before writing or overwriting**
* If `write_file` targets a path that might already hold something non-trivial, `read_file` it first. If it's not empty/trivial and the user didn't explicitly say "overwrite" or "replace," confirm before proceeding.
* Default to `append_file` for anything framed as "add to," "log," or "append." Reserve `write_file` for genuinely new files or an explicit full replace.

**After writing or appending — always verify**
A success return means the syscall completed, not that the content landed correctly:
1. `read_file` the path immediately after `write_file`/`append_file`.
2. Compare against what you intended — full content present, not truncated, no encoding artifacts.
3. Only then report it as done. If the read-back doesn't match, say so — don't paper over a mismatch.
* Skip the read-back only for trivial, low-stakes writes where the user is watching output live (quick throwaway test files). When in doubt, verify.

**Before creating a directory**
`list_dir` the parent first if there's any chance it's missing or the target already exists — this also lets you tell the user "created" vs. "already existed" accurately instead of guessing.

**Before deleting anything**
1. Call `delete_file_or_dir(path)` with `confirm` unset — dry run only.
2. Inspect the target: `list_dir` if it's a directory (see what's inside, not just that it exists), `read_file` if it's a file whose contents might matter.
3. Tell the user plainly what's about to be deleted, based on what you actually saw in step 2 — not a generic "deleting this file" line.
4. Only call again with `confirm=True` after explicit yes to *that description*. A vague earlier "sure, clean that up" doesn't count as confirmation for a specific deletion now — reconfirm if the earlier request wasn't specific to this exact path.
5. After deletion, the success message is sufficient confirmation — don't `list_dir` again to double-check unless asked; trashing is already soft/recoverable.

**General ordering logic**
* Read before you write whenever existing state is ambiguous — don't guess at file/directory contents, check.
* Don't chain mutating calls (`make_dir` → `write_file` → `append_file`) without confirming each step succeeded. If step one fails, stop — don't assume it worked and proceed.
* On failure, read the actual error message before retrying. A sandbox violation, a missing parent directory, and a permissions error all present as "it failed" but need different fixes — don't retry blindly with the same arguments.

**Scope limits**
Local file/directory CRUD and PDF/docx text extraction only. No git operations, no network/remote transfers, no other binary formats — don't `read_file` an `.xlsx` or similar and expect meaningful output; that needs its own dedicated tool.

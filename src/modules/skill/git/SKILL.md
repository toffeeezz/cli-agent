---
name: git_operations
desc: >-
  Provides basic git version control operations including checking repository
  status, staging files, committing changes, and viewing diffs. Wraps the
  `git` CLI directly and returns raw command output.
  Triggers: "git status", "stage this file", "commit these changes", "show me the diff",
  "what changed", "is this staged", "add to git", "check repo status".
  Do NOT use for generic file reading/writing/deletion, remote operations
  (push, pull, clone, fetch), branch management, merge/rebase, or any git
  command not explicitly listed below.
tools:
  - git_status
  - git_add
  - git_commit
  - git_diff
---
## Description
A collection of utility functions for interacting with a local git repository via subprocess calls to the `git` CLI. Each tool operates on a specified working directory and returns the raw stdout/stderr from the underlying git command, unmodified, so it should be read directly rather than re-interpreted.
---
## Tool API Reference
### 1. `git_status`
Runs `git status` in the given directory and returns the result.
* **Parameters:**
  * `path` (`str`): The filesystem path of the git repository to check.
* **Returns:** `tuple[bool, str]` — `(True, output)` on success, where output is the raw stdout of `git status` (branch info, staged/unstaged changes, untracked files) exactly as it would appear in a terminal. `(False, error_message)` on failure.
* **Note:** Present the full status report to the user in a table.
---
### 2. `git_add`
Stages a file with `git add` inside a given repository.
* **Parameters:**
  * `cwd_path` (`str`): The working directory of the git repository.
  * `file_path` (`str`): The path of the file to stage, relative to `cwd_path`.
* **Returns:** `tuple[bool, str]` — `(True, output)` on success, where output is stdout from `git add` (almost always empty — no output means it worked). `(False, error_message)` on failure.
---
### 3. `git_commit`
Creates a commit with the given message using `git commit`.
* **Parameters:**
  * `cwd_path` (`str`): The working directory of the git repository.
  * `commit_msg` (`str`): The commit message to use.
* **Returns:** `tuple[bool, str]` — `(True, output)` on success, where output confirms what was committed (e.g. `[main <hash>] <message>` plus a file-change summary) — read it to confirm the commit actually landed. `(False, error_message)` on failure.
---
### 4. `git_diff`
Shows the diff of a file using `git diff`.
* **Parameters:**
  * `cwd_path` (`str`): The working directory of the git repository.
  * `file_path` (`str`): The path of the file to diff, relative to `cwd_path`.
* **Returns:** `tuple[bool, str]` — `(True, output)` on success, where output is the unified diff (`+`/`-` prefixed lines). An empty string means no diff (file unchanged, or already staged). `(False, error_message)` on failure.
---
## Usage Guidelines & Safeguards
* **Failure modes:** All tools share the same three failure cases — `git` not found on PATH, a non-zero exit code from git (message includes git's own stderr), or a command timeout. Read the returned error message directly; it already tells you which of these occurred.
* **Order of operations:** Check `git_status` before staging or committing, so you know what's actually changed and where. Use `git_diff` on a specific file before staging it if you want to confirm exactly what will be committed.
* **Committing:** Only call `git_commit` once the relevant files have been staged with `git_add` — this module does not stage automatically, and does not support `git commit -a`.
* **Commit message tagging:** Whenever you call `git_commit`, if you were the one who modified, created, or deleted the changes, prefix the commit message with `[ame]` so it's clear the commit was made by you rather than the user directly — e.g. `[ame] Fix off-by-one error in memory session loading`. Otherwise, don not prefix it with anything. Don't ask the user for permission to add the tag, just include it; if the user gives you an exact commit message and asks you to use it verbatim, still prepend `[ame] ` to the front of it rather than skipping the tag. If user did not provide a commit message, create one by using `git_diff` to check what are the changes made.
* **Scope limits:** These tools only cover status, add, commit, and diff. Do not attempt to construct other git subcommands (push, pull, branch, merge, log, reset, etc.) through these functions — they are not general-purpose git wrappers.

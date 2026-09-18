---
name: git_operations
desc: >-
  Provides basic git version control operations including checking repository
  status, staging files, committing changes, viewing diffs, and restoring
  files. Wraps the `git` CLI directly and returns raw command output.
  Triggers: "git status", "stage this file", "commit these changes", "show me the diff",
  "what changed", "is this staged", "add to git", "check repo status",
  "discard changes", "unstage this file", "revert this file", "restore this file".
  Do NOT use for generic file reading/writing/deletion, remote operations
  (push, pull, clone, fetch), branch management, merge/rebase, or any git
  command not explicitly listed below.
tools:
  - git_status
  - git_add
  - git_commit
  - git_diff
  - git_restore
---
## Description
A collection of utility functions for interacting with a local git repository via subprocess calls to the `git` CLI. Each tool returns the raw stdout/stderr from the underlying git command, unmodified — read it directly rather than re-interpreting it. Full parameter and return-type signatures are already available via the tool-choice schema; this document covers only what that schema can't: sequencing, safety rules, and formatting conventions.

---
## Tool Quick Reference
Use this only to pick the right tool at a glance — see the schema for exact parameters.

| Tool | Purpose | Notes |
|---|---|---|
| `git_status` | Repo state: branch, staged/unstaged, untracked | Read-only. Always safe to call. |
| `git_add` | Stage one file | No output on success = it worked. |
| `git_commit` | Commit staged changes | Requires prior `git_add`; no `-a` support. |
| `git_diff` | Unified diff of one file | Empty output means unchanged **or** already staged — check `git_status` to tell which. |
| `git_restore` | Discard/unstage changes to one file | **Destructive** on working-tree targets — see safeguards below. |

---
## Usage Guidelines & Safeguards

**Order of operations**
1. Run `git_status` before staging, committing, or restoring anything — don't assume you know repo state from earlier in the conversation.
2. If `git_status` shows nothing staged and nothing modified for the file(s) in question, say so and stop — don't call `git_commit` against an empty diff, and don't call `git_restore` with nothing to restore.
3. Run `git_diff` on a specific file before staging or restoring it if you need to confirm exactly what will be committed or lost.

**Committing**
* Only call `git_commit` after the relevant file has been staged with `git_add` in this same turn — don't assume an earlier stage is still valid without checking `git_status` first.
* **One file, one add+commit cycle.** When committing multiple files, never stage everything at once with one combined message. For each file in sequence: `git_diff` it (if writing your own message), `git_add` it, `git_commit` it with a message specific to that file, then move to the next. Each file becomes its own commit — a shared generic message loses the specificity of what actually changed in each one.

**Restoring (destructive path)**
* Never call `git_restore` on a working-tree target (default, or explicit `--worktree`/`-W`) without first running `git_diff` on that file and showing the user what will be lost, then getting explicit confirmation.
* This confirmation step is **not** required for `--staged`-only restores — that just unstages, it doesn't touch working-tree contents.
* If the user says something ambiguous like "undo my changes to X," ask whether they mean unstage (`--staged`) or fully discard (working tree) before acting — these have very different consequences and should never be guessed.
* Never pass `-p`/`--patch` — interactive hunk selection needs a live terminal and will hang through a non-interactive subprocess call. If the user wants to restore only part of a file, read the diff yourself, describe which hunks would be discarded, and let them confirm restoring the whole file — or tell them to handle it manually.

**Commit message tagging**
* Prefix with `[ame]` only when *you* made the underlying change (modified/created/deleted the content being committed) — e.g. `[ame] Fix off-by-one error in memory session loading`.
* Do NOT prefix when the user made the changes and is just asking you to commit on their behalf — the commit should read as if the user wrote it.
* If the user gives an exact commit message, use it verbatim (still prepend `[ame] ` if applicable, never otherwise).

**Commit message format** (when you're writing it, not the user)
Inspect the actual diff first, then format as `<verb> <target>: <short description>`:
* `<verb>`: past-tense/descriptive — `refactored`, `fixed`, `added`, `removed`, `renamed`, `updated`, `deleted`.
* `<target>`: the file, module, class, or feature the change centers on.
* `<short description>`: plain-language summary of the change, not a restatement of diff syntax.
* Examples: `refactored gui: split chat bubble sizing into a separate helper` · `fixed memory_manager: corrected off-by-one in session loading` · `[ame] deleted handler.py: removed unused legacy request handler`.
* One line, under ~72 characters where possible. Add detail below a blank line only if the change genuinely spans multiple things — though that usually means it should be split into separate commits instead.

**Failure modes**
All tools share three failure cases: `git` not found on PATH, a non-zero exit from git (message includes git's own stderr), or a command timeout. The returned error message already identifies which — read it directly rather than re-diagnosing.

**Scope limits**
Status, add, commit, diff, restore — that's it. Do not construct other git subcommands (push, pull, branch, merge, log, reset, checkout, etc.) through these tools; they are not general-purpose git wrappers.

import subprocess


def git_status(path: str) -> tuple[bool, str]:
    """Run `git status` in the given directory and return the result.

    On success, the output string is exactly what you'd see from running
    ``git status`` in a terminal — branch info, staged/unstaged changes,
    untracked files. Read it directly to know what's going on. Present the full report
    in a table to user

    Args:
        path: The filesystem path of the git repository to check.

    Returns:
        A tuple of (success, output). On success, output is raw stdout from
        ``git status``. On failure, output is an error message describing what
        went wrong (e.g., git not found, non-zero exit, timeout).
    """
    try:
        result = subprocess.run(
            ["git", "status"], cwd=path, capture_output=True, text=True, check=True
        )
        return True, result.stdout
    except FileNotFoundError:
        return False, "Error: 'git' executable was not found on system PATH"
    except subprocess.CalledProcessError as e:
        return False, f"Error: Git returned exit code {e.returncode}:\n{e.stderr}"
    except subprocess.TimeoutExpired:
        return False, "Error: Command execution timed out."


def git_add(cwd_path: str, file_path: str) -> tuple[bool, str]:
    """Stage a file with `git add` inside a given repository.

    If it succeeds, stdout is almost always empty — ``git add`` doesn't
    print anything unless something's wrong. So a success means "it's
    staged now, move on."

    Args:
        cwd_path: The working directory of the git repository (equivalent to
                  the ``-C`` or ``cwd`` argument for git commands).
        file_path: The path of the file to stage, relative to cwd_path.

    Returns:
        A tuple of (success, output). On success, output is stdout from
        ``git add`` (usually empty). On failure, output is an error message
        describing what went wrong.
    """
    try:
        result = subprocess.run(
            ["git", "add", file_path],
            cwd=cwd_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return True, result.stdout
    except FileNotFoundError:
        return False, "Error: 'git' executable was not found on system PATH"
    except subprocess.CalledProcessError as e:
        return False, f"Error: Git returned exit code {e.returncode}:\n{e.stderr}"
    except subprocess.TimeoutExpired:
        return False, "Error: Command execution timed out."


def git_commit(cwd_path: str, commit_msg: str) -> tuple[bool, str]:
    """Create a commit with the given message using `git commit`.

    On success, the output string tells you what was committed — e.g.
    "[main <hash>] <message>" plus a file-change summary. Read it to
    confirm the commit actually landed.

    Args:
        cwd_path: The working directory of the git repository (equivalent to
                  the ``-C`` or ``cwd`` argument for git commands).
        commit_msg: The commit message to use for the commit.

    Returns:
        A tuple of (success, output). On success, output is stdout from
        ``git commit``. On failure, output is an error message describing what
        went wrong (e.g., git not found, non-zero exit, timeout).
    """
    try:
        result = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=cwd_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return True, result.stdout
    except FileNotFoundError:
        return False, "Error: 'git' executable was not found on system PATH"
    except subprocess.CalledProcessError as e:
        return False, f"Error: Git returned exit code {e.returncode}:\n{e.stderr}"
    except subprocess.TimeoutExpired:
        return False, "Error: Command execution timed out."


def git_diff(cwd_path: str, file_path: str) -> tuple[bool, str]:
    """Show the diff of a file using `git diff`.

    On success, the output string is the unified diff (lines with ``+``/``-``
    prefixes). If there's no diff (file hasn't changed or is already staged),
    you get back an empty string. Read it to see exactly what's changed
    line-by-line.

    Args:
        cwd_path: The working directory of the git repository (equivalent to
                  the ``-C`` or ``cwd`` argument for git commands).
        file_path: The path of the file to diff, relative to cwd_path.

    Returns:
        A tuple of (success, output). On success, output is stdout from
        ``git diff``. On failure, output is an error message describing what
        went wrong (e.g., git not found, non-zero exit, timeout).
    """
    try:
        result = subprocess.run(
            ["git", "diff", file_path],
            cwd=cwd_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return True, result.stdout
    except FileNotFoundError:
        return False, "Error: 'git' executable was not found on system PATH"
    except subprocess.CalledProcessError as e:
        return False, f"Error: Git returned exit code {e.returncode}:\n{e.stderr}"
    except subprocess.TimeoutExpired:
        return False, "Error: Command execution timed out."

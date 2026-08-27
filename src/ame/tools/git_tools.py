import asyncio
import subprocess

from ame.tools.tool_registry import tool_registry


@tool_registry.register()
def git_status(path: str) -> tuple[bool, str]:
    """Run `git status` in the given directory and return the result.

    Args:
        path: The filesystem path of the git repository to check.

    Returns:
        A tuple of (success, output). On success, output is the stdout from
        `git status`. On failure, output is an error message describing what
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


@tool_registry.register()
def git_add(cwd_path: str, file_path: str) -> tuple[bool, str]:
    """Stage a file with `git add` inside a given repository.

    Args:
        cwd_path: The working directory of the git repository (equivalent to
                  the `-C` or `cwd` argument for git commands).
        file_path: The path of the file to stage, relative to cwd_path.

    Returns:
        A tuple of (success, output). On success, output is the stdout from
        `git add` (usually empty). On failure, output is an error message
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
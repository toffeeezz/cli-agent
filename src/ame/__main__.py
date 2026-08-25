import asyncio

from rich.prompt import Prompt

from ame.cli.interface import run_cli

# Removes the default built-in suffix
Prompt.prompt_suffix = ""


def main() -> None:
    asyncio.run(run_cli())

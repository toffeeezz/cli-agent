import argparse
import asyncio
from argparse import Namespace

from rich.prompt import Prompt

from ame.cli.interface import run_cli
from ame.cli.renderer import console
from ame.settings.settings import get_settings
from ame.tools.file_tools import *

# Removes the default built-in suffix
Prompt.prompt_suffix = ""


def parse_args() -> Namespace:
    parser = argparse.ArgumentParser(
        prog="cli-agent", description="An agent/companion assitant"
    )
    _ = parser.add_argument("--dev", action="store_true", help="Enable developer mode")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    get_settings().dev_mode = args.dev
    console.print(args.dev)
    asyncio.run(run_cli())

import argparse
import asyncio
from argparse import Namespace

from rich.prompt import Prompt

from ame.agent.agent import Agent
from ame.cli.interface import run_cli
from ame.gui.app import main_app
from ame.settings.settings import get_settings
from ame.tools.file_tools import *
from ame.utils.logger import setup_logging

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
    setup_logging()
    get_settings().dev_mode = args.dev
    asyncio.run(run_cli())

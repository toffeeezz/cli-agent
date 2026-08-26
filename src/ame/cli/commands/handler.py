import asyncio
from typing import Literal, cast

from rich.table import Table

from ame.cli.commands.command_registry import command_registry
from ame.cli.renderer import console, render_hidden_prompt, render_multiline_prompt
from ame.settings.settings import get_settings
from ame.utils import logger
from ame.tools.tool_registry import tool_registry


class ExitCLI(Exception):
    """Raise to exit the program"""


@command_registry.register(flag="/tool", dev_command=True)
async def execute_tool(name: str, *raw_pairs: str) -> None:
    """Directly invokes a registered tool by name using key=value args."""
    kwargs = cast(
        dict[str, object],
        dict(pair.split(sep="=", maxsplit=1) for pair in raw_pairs),
    )
    _, msg = await tool_registry.execute(name=name, kwargs=kwargs)
    console.print(f"[bold yellow] \\[Tool Message]: {msg}")


@command_registry.register("/help")
def print_help() -> None:
    """displays a table containing a list of all commands"""
    command_list = command_registry.command_list
    table = Table(show_header=True, header_style="bold", padding=(0, 4), leading=1)
    table.add_column("Command", style="italic orange3", justify="center")
    table.add_column("Required Args", style="bold", justify="center")
    table.add_column("Optional Args", style="bold", justify="center")
    table.add_column("Description", style="green", justify="left")

    for command in command_list.values():
        if command.dev_command and not get_settings().dev_mode:
            continue
        table.add_row(
            command.flag,
            f"{', '.join(arg.lower() for arg in command.required_args)}",
            f"{', '.join(arg.lower() for arg in command.optional_args)}",
            command.desc,
        )

    console.print(table)
    console.print("USAGE: \\[command] \\[args]")
    console.print("[bold yellow]IMPORTANT: Arguments must be entered in order")


@command_registry.register("/exit")
def exit() -> None:
    """exits the program"""
    raise ExitCLI


@command_registry.register("/env")
def display_settings() -> None:
    """displays the environment variables"""
    settings = get_settings()
    table = Table(show_header=True, header_style="bold", padding=(0, 4))
    table.add_column("Environments", style="bold blue")
    table.add_column("Value", style="italic")

    for setting in settings.model_dump():
        if setting == "api_key" and not settings.dev_mode:
            table.add_row(setting, "******************")
            continue
        table.add_row(setting, str(getattr(settings, setting)))

    console.print(table)


@command_registry.register("/clear")
def clear_console() -> None:
    """clears the terminal output"""
    console.clear()


@command_registry.register("/multi_line")
def enter_multi_line_edit() -> str:
    """enters a mode allowing pasting of long multi-line paragraphs or code"""
    return render_multiline_prompt()


@command_registry.register("/model")
def select_model(model_name: str):
    """see all avaialable models by your service provider"""
    settings = get_settings()
    settings.llm_model = model_name


@command_registry.register("/api_url")
def select_url(api_url: str) -> None:
    """the url endpoint of your service provider"""
    settings = get_settings()
    settings.api_url = api_url


@command_registry.register("/api_key")
def select_key() -> None:
    """the api key from your service provider"""
    api_key = render_hidden_prompt()
    settings = get_settings()
    settings.api_key = api_key


@command_registry.register("/logging")
def show_logs(level: Literal["none", "warning", "debug", "info"]) -> None:
    settings = get_settings()
    settings.console_logging = level
    logger.set_console_level(level)

from rich.table import Table

from ame.cli.commands.command_registry import registry
from ame.cli.renderer import console, render_hidden_prompt, render_multiline_prompt
from ame.settings.settings import get_settings


class ExitCLI(Exception):
    """Raise to exit the program"""


@registry.register("/help")
def print_help() -> None:
    """displays a table containing a list of all commands"""
    command_list = registry.command_list
    table = Table(show_header=True, header_style="bold", padding=(0, 4), leading=1)
    table.add_column("Command", style="italic orange3", justify="center")
    table.add_column("Required Args", style="bold", justify="center")
    table.add_column("Optional Args", style="bold", justify="center")
    table.add_column("Description", style="green", justify="left")

    for command in command_list.values():
        table.add_row(
            command.flag,
            f"{', '.join(arg.lower() for arg in command.required_args)}",
            f"{', '.join(arg.lower() for arg in command.optional_args)}",
            command.desc,
        )

    console.print(table)
    console.print("USAGE: \\[command] \\[args]")
    console.print("[bold yellow]IMPORTANT: Arguments must be entered in order")


@registry.register("/exit")
def exit() -> None:
    """exits the program"""
    raise ExitCLI


@registry.register("/env")
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


@registry.register("/clear")
def clear_console() -> None:
    """clears the terminal output"""
    console.clear()


@registry.register("/multi_line")
def enter_multi_line_edit() -> str:
    """enters a mode allowing pasting of long multi-line paragraphs or code"""
    return render_multiline_prompt()


@registry.register("/model")
def select_model(model_name: str):
    """see all avaialable models by your service provider"""
    settings = get_settings()
    settings.llm_model = model_name


@registry.register("/api_url")
def select_url(api_url: str) -> None:
    """the url endpoint of your service provider"""
    settings = get_settings()
    settings.api_url = api_url


@registry.register("/api_key")
def select_key() -> None:
    """the api key from your service provider"""
    api_key = render_hidden_prompt()
    settings = get_settings()
    settings.api_key = api_key

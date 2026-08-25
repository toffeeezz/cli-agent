import getpass
import readline

from rich.console import Console
from rich.markdown import Markdown

console = Console()


def user_prompt() -> str:
    user: str = f"[blue bold]{getpass.getuser()}[/]"
    prompt = f"|[{user}]| >> "

    return prompt


def agent_prompt(agent_name: str = "Ame") -> str:
    agent: str = f"[yellow bold]{agent_name}[/]"
    prompt = f"|[{agent}]| >> "
    return prompt


def render_agent_text(text: str) -> None:
    md = Markdown(text)
    console.print(agent_prompt(), md, end="")


def render_user_prompt() -> str:
    with console.capture() as capture:
        console.print(user_prompt(), end="")
    agent_prompt = capture.get()

    return input(agent_prompt)


def render_multiline_prompt() -> str:
    console.print(
        "[bold cyan]\n╔════ Multi-Line Prompt Mode ════════════════════════════════════╗[/bold cyan]"
    )
    console.print(
        "[dim] Paste your text. Press [bold green]Enter twice[/bold green] on an empty line to submit. [/dim]"
    )
    console.print(
        "[bold cyan]╚════════════════════════════════════════════════════════════════╝[/bold cyan]"
    )

    lines = []
    line_count = 1

    while True:
        try:
            line = input(f" {line_count:02d} | ")
            if line == "":
                break
            lines.append(line)
            line_count += 1
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]! Paste mode cancelled.[/yellow]")
            return ""

    full_text = "\n".join(lines)
    console.print(f"[green]✔[/green] Captured {len(lines)} lines.")

    return full_text


def render_hidden_prompt() -> str:
    with console.capture() as capture:
        console.print("[yellow bold]<SECURED PROMPT>[/]", user_prompt(), end="")
    ansi_prompt = capture.get()

    old_history_len = readline.get_current_history_length()

    # temporarliy disables the history
    try:
        secret_input = getpass.getpass(prompt=ansi_prompt)
    finally:
        new_history_len = readline.get_current_history_length()
        if new_history_len > old_history_len:
            readline.remove_history_item(new_history_len - 1)

    return secret_input


def render_cli_text(text: str) -> None:
    md = Markdown(text)
    console.print(agent_prompt(), md, end="")

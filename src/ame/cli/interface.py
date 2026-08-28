import readline

from ame.agent.agent import agent
from ame.cli.commands.command_registry import command_registry
from ame.cli.commands.handler import ExitCLI
from ame.cli.renderer import (
    console,
    render_agent_text,
    render_thinking_spinner,
    render_user_prompt,
)
from ame.errors import ProgramError
from ame.settings.settings import get_settings
from ame.tools import git_tools


def command_completer():
    """Dynamically creates a completion function based on your registered commands."""

    def completer(text: str, state: int) -> str | None:
        options = [cmd for cmd in command_registry.command_list]
        matches = [opt for opt in options if opt.startswith(text)]

        if state < len(matches):
            return matches[state]
        return None

    return completer


readline.set_completer(command_completer())
readline.parse_and_bind("tab: complete")
readline.set_completer_delims(readline.get_completer_delims().replace("/", ""))


async def run_cli() -> None:
    text_buffer: list[str] = []

    console.print(
        "[bold green]\nCLI Session Initialized.[/bold green] Type [cyan]/help[/cyan] for commands."
    )

    if get_settings().dev_mode:
        console.print("[bold yellow]Currently running in dev mode")

    while True:
        try:
            if text_buffer:
                prompt_prefix = f"[dim]({len(text_buffer)} lines buffered)[/dim] "
                console.print(prompt_prefix, end="")

            user_input = render_user_prompt().strip()
            if not user_input:
                if text_buffer:
                    full_payload = "\n".join(text_buffer)
                    with render_thinking_spinner():
                        async for chunk in agent.get_reply(full_payload):
                            render_agent_text(chunk)
                    text_buffer.clear()
                continue

            if user_input.startswith("/"):
                parts = user_input.split()
                flag = parts[0]
                command_args = parts[1:]

                if flag not in command_registry.command_list:
                    console.print(
                        f"[bold red]Unknown command: {flag}. Type /help[/bold red]"
                    )
                    continue

                result = await command_registry.execute(flag, *command_args)

                if flag == "/multi_line_mode" and isinstance(result, str) and result:
                    text_buffer.extend(result.splitlines())
                    console.print(
                        "[dim italic]💡 Tip: Press Enter on an empty line to submit your buffer, or type more text.[/dim italic]"
                    )

                continue

            if text_buffer:
                text_buffer.append(user_input)
                console.print(
                    f"[dim]Line added to buffer ({len(text_buffer)} total). Press Enter on a blank line to send.[/dim]"
                )
                continue

            with render_thinking_spinner():
                async for chunk in agent.get_reply(user_input):
                    render_agent_text(chunk)

        except ExitCLI:
            console.print("\n[bold red]Terminating session. Goodbye![/bold red]")
            break
        except ProgramError as e:
            console.print(f"[bold red]Error: {e}[/bold red]")
        except (KeyboardInterrupt, EOFError):
            if text_buffer:
                text_buffer.clear()
                console.print("\n[yellow]Workspace buffer flushed clean.[/yellow]")
            else:
                console.print("\n[yellow]Use /exit to shut down safely.[/yellow]")

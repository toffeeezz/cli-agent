import readline

from ame.cli.commands.handler import *
from ame.cli.commands.command_registry import registry
from ame.cli.renderer import console, render_user_prompt
from ame.errors import ProgramError


def command_completer():
    """Dynamically creates a completion function based on your registered commands."""

    def completer(text: str, state: int) -> str | None:
        options = [cmd for cmd in registry.command_list]
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

    while True:
        try:
            # Adapt prompt visually if there is text waiting in the buffer
            if text_buffer:
                prompt_prefix = f"[dim]({len(text_buffer)} lines buffered)[/dim] "
                console.print(prompt_prefix, end="")

            user_input = render_user_prompt().strip()
            if not user_input:
                if text_buffer:
                    full_payload = "\n".join(text_buffer)
                    text_buffer.clear()
                continue

            # COMMAND TRACKING BLOCK
            if user_input.startswith("/"):
                parts = user_input.split()
                flag = parts[0]
                command_args = parts[1:]

                if flag not in registry.command_list:
                    console.print(
                        f"[bold red]Unknown command: {flag}. Type /help[/bold red]"
                    )
                    continue

                command_info = registry.command_list[flag]

                result = registry.execute(flag, *command_args)

                if flag == "/multi_line" and isinstance(result, str) and result:
                    # Split lines up to allow editing/accumulation in the buffer seamlessly
                    text_buffer.extend(result.splitlines())
                    console.print(
                        "[dim italic]💡 Tip: Press Enter on an empty line to submit your buffer, or type more text.[/dim italic]"
                    )

                continue  # Skip agent execution to stay in the prompt loop

            # CHAT MODE TRACKING BLOCK
            if text_buffer:
                text_buffer.append(user_input)
                console.print(
                    f"[dim]Line added to buffer ({len(text_buffer)} total). Press Enter on a blank line to send.[/dim]"
                )

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

import inspect
from collections.abc import Callable
from typing import ParamSpec, TypeVar, cast, final

from pydantic import BaseModel, TypeAdapter, ValidationError

from ame.errors import ProgramError
from ame.settings.settings import get_settings

P = ParamSpec("P")
R = TypeVar("R")


class Command(BaseModel):
    flag: str
    desc: str
    required_args: list[str]
    optional_args: list[str]
    dev_command: bool = False
    invoke: Callable[..., object]


class CommandLineError(ProgramError):
    flag: str

    def __init__(self, flag: str, message: str) -> None:
        self.flag = flag
        super().__init__(message)


@final
class CommandNotFoundError(CommandLineError):
    def __init__(self, flag: str) -> None:
        super().__init__(
            flag=flag,
            message=f"Unknown command: '{flag}' Type /help to list all available commands",
        )


@final
class CommandNumArgsError(CommandLineError):
    def __init__(self, command: Command, provided_count: int) -> None:
        required_args = command.required_args
        super().__init__(
            flag=command.flag,
            message=f"Command has an invalid number of arguments: Expected {len(required_args)}, but got {provided_count} instead",
        )


@final
class CommandArgsTypeError(CommandLineError):
    def __init__(self, flag: str, args: str) -> None:
        super().__init__(flag, message=f"Unexpected argument type: {args}")


class CommandRegistry:
    def __init__(self) -> None:
        self.command_list: dict[str, Command] = {}

    def register(
        self, flag: str, dev_command: bool = False
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:

        def decorator(func: Callable[P, R]) -> Callable[P, R]:
            doc = inspect.getdoc(func) or ""
            sig = inspect.signature(func)

            required_args: list[str] = []
            optional_args: list[str] = []

            for name, param in sig.parameters.items():
                if param.default is inspect.Parameter.empty:
                    required_args.append(name)
                else:
                    optional_args.append(name)

            self.command_list[flag] = Command(
                flag=flag,
                desc=doc,
                dev_command=dev_command,
                required_args=required_args,
                optional_args=optional_args,
                invoke=func,
            )
            return func

        return decorator

    async def execute(self, flag: str, *args: object) -> object:
        command = self.command_list.get(flag)
        if not command or (command.dev_command and not get_settings().dev_mode):
            raise CommandNotFoundError(flag)

        sig = inspect.signature(command.invoke)

        bound_args = sig.bind_partial(*args)
        merged_kwargs = bound_args.arguments

        missing_required = [
            name for name in command.required_args if name not in merged_kwargs
        ]
        if missing_required:
            raise CommandNumArgsError(command, provided_count=len(args))

        for name, param in sig.parameters.items():
            if (
                name not in merged_kwargs
                and param.default is not inspect.Parameter.empty
            ):
                merged_kwargs[name] = param.default

        validated_kwargs: dict[str, object] = {}
        try:
            for name, param in sig.parameters.items():
                if name in merged_kwargs:
                    value = merged_kwargs[name]
                    if (
                        param.annotation is inspect.Parameter.empty
                        or param.annotation is object
                    ):
                        validated_kwargs[name] = value
                    elif param.kind is inspect.Parameter.VAR_POSITIONAL:
                        adapter = TypeAdapter(param.annotation)
                        validated_kwargs[name] = tuple(
                            adapter.validate_python(item) for item in value
                        )
                    else:
                        adapter = TypeAdapter(param.annotation)
                        validated_kwargs[name] = adapter.validate_python(value)
        except ValidationError as e:
            raise CommandArgsTypeError(flag, f"{e}") from e

        call_args: list[object] = []
        call_kwargs: dict[str, object] = {}
        for name, param in sig.parameters.items():
            if name not in validated_kwargs:
                continue
            if param.kind in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            ):
                call_args.append(validated_kwargs[name])
            elif param.kind is inspect.Parameter.VAR_POSITIONAL:
                call_args.extend(cast(tuple[object, ...], validated_kwargs[name]))
            else:
                call_kwargs[name] = validated_kwargs[name]

        result = command.invoke(*call_args, **call_kwargs)
        if inspect.isawaitable(result):
            return await result
        return result


command_registry = CommandRegistry()

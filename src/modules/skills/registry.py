import asyncio
import functools
import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import ParamSpec, TypeVar, get_type_hints

from openai.types.chat import ChatCompletionToolUnionParam
from pydantic import TypeAdapter

from modules.skills.errors import ToolArgumentError, ToolError, ToolNotFoundError

P = ParamSpec("P")
R = TypeVar("R")


@dataclass
class ToolEntry:
    function: Callable[..., object]
    schema: ChatCompletionToolUnionParam


class ToolRegistry:
    def __init__(self) -> None:
        self.tools: dict[str, ToolEntry] = {}

    def register(self, namespace: str, func: Callable[P, R]) -> Callable[P, R]:

        sig = inspect.signature(func)
        hints = get_type_hints(func)

        properties: dict[str, object] = {}
        required: list[str] = []

        for name, param in sig.parameters.items():
            if name == "self":
                continue
            param_type = hints.get(name, str)
            properties[name] = TypeAdapter(param_type).json_schema()
            if param.default is inspect.Parameter.empty:
                required.append(name)

        tool_name = f"{namespace}.{func.__name__}"

        self.tools[tool_name] = ToolEntry(
            function=func,
            schema={
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": func.__doc__ or "",
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                    },
                },
            },
        )
        return func

    def unregister(self, namespace: str) -> None:
        prefix = f"{namespace}."
        self.tools = {k: v for k, v in self.tools.items() if not k.startswith(prefix)}

    @property
    def schema(self) -> list[ChatCompletionToolUnionParam]:
        tools: list[ChatCompletionToolUnionParam] = [
            _.schema for _ in self.tools.values()
        ]
        return tools

    @property
    def functions(self):
        functions = [function.function for function in self.tools.values()]
        return functions

    async def execute_tool(
        self, name: str, kwargs: dict[str, object]
    ) -> tuple[bool, object]:
        """Tries to execute the given tool and its arguments. Throws ToolNotFoundError, ToolArgumentError, ToolError"""
        if name not in self.tools:
            raise ToolNotFoundError(name)

        tool = self.tools[name]
        loop = asyncio.get_running_loop()
        try:
            if inspect.iscoroutinefunction(tool.function):
                result = await tool.function(**kwargs)
            else:
                result = await loop.run_in_executor(
                    None, functools.partial(tool.function, **kwargs)
                )

            if not (
                isinstance(result, tuple)
                and len(result) == 2
                and isinstance(result[0], bool)
            ):
                raise ToolError(
                    name, f"Tool '{name}' did not return (bool, Any) as expected"
                )
            return result
        except TypeError as e:
            raise ToolArgumentError(name, str(e)) from e
        except Exception as e:
            raise ToolError(name, f"Execution of tool '{name}' failed: {e}") from e

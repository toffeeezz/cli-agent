from collections.abc import Callable
import inspect
from typing import ParamSpec, TypeVar, final, get_type_hints
from openai.types.chat import ChatCompletionToolUnionParam
from pydantic import BaseModel, TypeAdapter

from ame.errors import ProgramError


class Tool(BaseModel):
    invoke: Callable[..., tuple[bool, object]]
    tool_schema: ChatCompletionToolUnionParam


class ToolRequest(BaseModel):
    tool: Tool
    require_confirmation: bool


P = ParamSpec("P")
R = TypeVar("R")


class ToolError(ProgramError):
    tool_name: str

    def __init__(self, tool_name: str, message: str) -> None:
        self.tool_name = tool_name
        super().__init__(message)


@final
class ToolNotFoundError(ToolError):
    def __init__(self, tool_name: str) -> None:
        super().__init__(
            tool_name,
            f"Tool '{tool_name}' may not be registered or it simply does not exist",
        )


@final
class ToolArgumentError(ToolError):
    def __init__(self, tool_name: str, tool_arg: str) -> None:
        super().__init__(
            tool_name,
            f"Tool '{tool_name}' has an invalid argument: {tool_arg}",
        )


@final
class ToolRegistry:
    def __init__(self) -> None:
        self._tool_list: dict[str, Tool] = {}

    def register(
        self,
    ) -> Callable[[Callable[P, tuple[bool, object]]], Callable[P, tuple[bool, object]]]:
        def decorator(
            func: Callable[P, tuple[bool, object]],
        ) -> Callable[P, tuple[bool, object]]:
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

            self._tool_list[func.__name__] = Tool(
                invoke=func,
                tool_schema={
                    "type": "function",
                    "function": {
                        "name": func.__name__,
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

        return decorator

    @property
    def schemas(self) -> list[ChatCompletionToolUnionParam]:
        tools: list[ChatCompletionToolUnionParam] = [
            tool.tool_schema for tool in self._tool_list.values()
        ]
        return tools

    async def execute(
        self, name: str, kwargs: dict[str, object]
    ) -> tuple[bool, object]:
        """Tries to execute the given tool and its arguments. Throws ToolNotFoundError, ToolArgumentError, ToolError"""
        if name not in self._tool_list:
            raise ToolNotFoundError(name)

        tool = self._tool_list[name]
        try:
            if inspect.iscoroutinefunction(tool.invoke):
                result: tuple[bool, object] = await tool.invoke(**kwargs)
            else:
                result = tool.invoke(**kwargs)

            return result
        except TypeError as e:
            raise ToolArgumentError(name, str(e)) from e
        except Exception as e:
            raise ToolError(name, f"Execution of tool '{name}' failed: {e}") from e


registry = ToolRegistry()

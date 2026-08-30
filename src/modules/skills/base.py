import inspect
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import ParamSpec, TypeVar, final, get_type_hints

from openai.types.chat import ChatCompletionToolUnionParam
from pydantic import BaseModel, ConfigDict, TypeAdapter

from modules.core.errors import ProgramError

P = ParamSpec("P")
R = TypeVar("R")


@dataclass
class ToolEntry:
    callable: Callable[..., object]
    schema: ChatCompletionToolUnionParam


class ToolRequest(BaseModel):
    message: str
    tool_name: str
    confirm: bool = False


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolEntry] = {}

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

        self._tools[tool_name] = ToolEntry(
            callable=func,
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

    @property
    def schema(self) -> list[ChatCompletionToolUnionParam]:
        tools: list[ChatCompletionToolUnionParam] = [
            _.schema for _ in self._tools.values()
        ]
        return tools

    async def execute_tool(
        self, name: str, kwargs: dict[str, object]
    ) -> tuple[bool, object]:
        """Tries to execute the given tool and its arguments. Throws ToolNotFoundError, ToolArgumentError, ToolError"""
        if name not in self._tools:
            raise ToolNotFoundError(name)

        tool = self._tools[name]
        try:
            if inspect.iscoroutinefunction(tool.callable):
                result = await tool.callable(**kwargs)
            else:
                result = tool.callable(**kwargs)

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


class PythonTool(BaseModel):
    name: str
    is_async: bool
    args: list[str]


class SkillData(BaseModel):
    name: str
    desc: str
    version: str
    tools: list[str]
    path: Path


class Skill(BaseModel):
    name: str
    tool_registry: ToolRegistry
    model_config = ConfigDict(arbitrary_types_allowed=True)


class SkillModuleError(ProgramError):
    def __init__(self, msg: str) -> None:
        super().__init__(msg)


class SkillMissingMD(ProgramError):
    def __init__(self, skill_path: Path) -> None:
        super().__init__(
            f"An error occured while loading skill {skill_path}: Missing SKILL.md file"
        )


class SkillInvalidMD(ProgramError):
    def __init__(self, skill_path: Path, syntax: str) -> None:
        super().__init__(
            f"An error occured while loading skill {skill_path}: Invalid YAML syntax -> {syntax}"
        )


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

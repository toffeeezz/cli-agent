from pathlib import Path
from typing import final

from modules.core.errors import ProgramError


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


@final
class SKillNotFoundError(SkillModuleError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Trying to get an unknown skill: {name}")


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

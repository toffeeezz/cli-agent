from pathlib import Path
from typing import Callable

from pydantic import BaseModel, ConfigDict

from modules.skills.registry import ToolRegistry


class ToolRequest(BaseModel):
    message: str
    tool_name: str
    confirm: bool = False


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
    tools: list[Callable[..., object]]
    model_config = ConfigDict(arbitrary_types_allowed=True)

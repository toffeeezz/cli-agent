from pathlib import Path

from pydantic import BaseModel


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

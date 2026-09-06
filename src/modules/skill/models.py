from collections.abc import Callable

from openai.types.chat import ChatCompletionToolUnionParam
from pydantic import BaseModel


class Tool(BaseModel):
    name: str
    tool_func: Callable[..., tuple[bool, object]]
    tool_schema: ChatCompletionToolUnionParam


class SKillData(BaseModel):
    name: str
    desc: str
    tools: list[str]


class Skill(BaseModel):
    name: str
    instructions: str
    tool_names: list[str]
    tool_list: dict[str, Tool]


class SkillEntry(BaseModel):
    name: str
    desc: str
    skill: Skill


class ToolResult(BaseModel):
    name: str = ""
    skill_name: str = ""
    success: bool
    value: object

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field

_ = load_dotenv()


class AgentConfig(BaseModel):
    name: str = "Ame"
    system_prompt_path: Path = (
        Path(__file__).resolve().parent.parent.parent.parent / "SYSTEM_PROMPT.md"
    )
    backend: Literal["koboldcpp", "proxy"] = "proxy"
    url: str = "https://openrouter.ai/api/v1"
    api_key: str = Field(exclude=True, default=os.getenv("api_key") or "")
    model: str = "deepseek/deepseek-v4-flash"
    temperature: float = 0.6
    stream: bool = False
    max_loops: int = 40
    max_completion_tokens: int | None = None
    reasoning_effort: Literal["low", "medium", "high"] = "high"


class Config(BaseModel):
    username: str = "John"
    agent: AgentConfig = AgentConfig()

from typing import Literal

from openai import BaseModel


class AgentConfig(BaseModel):
    name: str = "Ame"
    backend: Literal["koboldcpp", "proxy"] = "proxy"
    url: str = "https://openrouter.ai/api/v1"
    model: str = "deepseek/deepseek-v4-flash"
    temperature: float = 0.6
    stream: bool = False
    max_loops: int = 40
    max_completion_tokens: int | None = None


class Config(BaseModel):
    agent: AgentConfig = AgentConfig()

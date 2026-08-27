from functools import lru_cache
from pathlib import Path
from typing import Literal, final

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent.parent.parent
)  # adjust based on actual depth


class Settings(BaseSettings):
    api_url: str = "https://openrouter.ai/api/v1"
    api_key: str = ""
    llm_model: str = "deepseek/deepseek-v4-flash"
    llm_system_prompt: Path = PROJECT_ROOT / "DEFAULT_SYSTEM_PROMPT.md"

    max_agent_loops: int = 20

    dev_mode: bool = False
    console_logging: Literal["none", "warning", "debug", "info"] = "none"

    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

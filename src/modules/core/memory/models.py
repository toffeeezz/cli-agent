from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

from modules.skill.models import Skill


class Memory(BaseModel):
    speaker: str
    message: ChatCompletionMessageParam
    timestamp: str
    importance_score: float


class MemorySession(BaseModel):
    start_date: str
    registered_skills: list[str] = []
    memories: list[Memory] = []

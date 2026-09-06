from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel


class Memory(BaseModel):
    speaker: str
    message: ChatCompletionMessageParam
    timestamp: str
    importance_score: float


class MemorySession(BaseModel):
    start_date: str
    memories: list[Memory] = []

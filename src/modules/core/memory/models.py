from pydantic import BaseModel


class Memory(BaseModel):
    speaker: str
    # [ame] changed from ChatCompletionMessageParam to dict to avoid
    # Pydantic serialization issues with OpenAI TypedDict unions on session load
    message: dict
    timestamp: str
    importance_score: float


class MemorySession(BaseModel):
    start_date: str
    registered_skills: list[str] = []
    memories: list[Memory] = []
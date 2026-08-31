from pydantic import BaseModel


class Memory(BaseModel):
    speaker: str
    content: str
    timestamp: str

import datetime

from modules.memory.models import Memory


class MemorySystem:
    def __init__(self) -> None:
        self.short_term: list[Memory] = []

    def save_memory(self, speaker: str, content: str) -> None:

        timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S")
        memory = Memory(speaker=speaker, content=content, timestamp=timestamp)

        self.short_term.append(memory)

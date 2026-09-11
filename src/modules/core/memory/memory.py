import asyncio
import datetime
import logging

from openai.types.chat import ChatCompletionMessageParam

from modules.core.memory.models import Memory, MemorySession

logger = logging.getLogger(__name__)


class MemoryManager:
    current_session: MemorySession

    def __init__(self, session: MemorySession) -> None:
        self.current_session = session

    def load_session(self, session: MemorySession) -> None:
        self.current_session = session
        logger.info(f"Loaded a session. New memories:\n{self.messages}")

    async def save_session(self, path: str) -> None:
        await asyncio.to_thread(self._write_session, path)

    def _write_session(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as file:
            _ = file.write(self.current_session.model_dump_json(indent=4))

    def add_message(self, message: ChatCompletionMessageParam) -> None:
        timestamp = datetime.datetime.now(datetime.UTC).strftime("%D %I:%M:%S %p")
        speaker = message.get("name") or ""
        memory = Memory(
            speaker=speaker,
            message=message,
            timestamp=timestamp,
            importance_score=1,
        )
        self.current_session.memories.append(memory)

    def dump_messages(
        self, messages: list[tuple[str, ChatCompletionMessageParam]]
    ) -> None:
        for timestamp, message in messages:
            speaker = message.get("name") or ""
            memory = Memory(
                speaker=speaker,
                message=message,
                timestamp=timestamp,
                importance_score=1,
            )
            self.current_session.memories.append(memory)

    @property
    def messages(self) -> list[ChatCompletionMessageParam]:
        messages: list[ChatCompletionMessageParam] = []
        for memory in self.current_session.memories:
            messages.append(memory.message)
        return messages

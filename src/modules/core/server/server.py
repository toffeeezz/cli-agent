import os

from dotenv import load_dotenv
from openai import AsyncOpenAI, AsyncStream
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionChunk,
)

from modules.config.models import AgentConfig
from modules.core.server.backend import OpenAiServer
from modules.core.server.models import ServerPayload

_ = load_dotenv()
API_KEY = os.environ.get("api_key")
KOBOLDCPP_URL = "http://localhost:5001/v1/chat/completions"


class Server:
    backend: OpenAiServer
    client: AsyncOpenAI

    def __init__(self, config: AgentConfig) -> None:
        self.backend = OpenAiServer()
        self.client = AsyncOpenAI(base_url=config.url, api_key=API_KEY)

    async def send_request(
        self, payload: ServerPayload
    ) -> tuple[bool, str, AsyncStream[ChatCompletionChunk] | ChatCompletion | None]:

        if payload.config.backend == "koboldcpp" or API_KEY is None:
            self.client.base_url = KOBOLDCPP_URL
            self.client.api_key = "koboldcpp"
        else:
            self.client.base_url = payload.config.url
            self.client.api_key = API_KEY

        if not payload.config.stream:
            return await self.backend.request_client_non_streaming(
                self.client,
                {
                    "model": payload.config.model,
                    "messages": payload.messages,
                    "max_completion_tokens": payload.config.max_completion_tokens,
                    "temperature": payload.config.temperature,
                    "tools": payload.tools,
                },
            )
        else:
            return await self.backend.request_client_streaming(
                self.client,
                {
                    "model": payload.config.model,
                    "messages": payload.messages,
                    "max_completion_tokens": payload.config.max_completion_tokens,
                    "temperature": payload.config.temperature,
                    "tools": payload.tools,
                    "stream": True,
                },
            )

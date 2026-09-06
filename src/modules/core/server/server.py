from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    AsyncStream,
    AuthenticationError,
    BadRequestError,
    OpenAIError,
    RateLimitError,
)
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionChunk,
)
from openai.types.chat.completion_create_params import (
    CompletionCreateParamsNonStreaming,
    CompletionCreateParamsStreaming,
)

from modules.core.server.models import ServerPayload


class Server:
    client: AsyncOpenAI

    def __init__(self, client: AsyncOpenAI) -> None:
        self.client = client

    async def send_request(
        self, payload: ServerPayload, stream: bool
    ) -> tuple[bool, str, AsyncStream[ChatCompletionChunk] | ChatCompletion | None]:
        if stream:
            return await self._request_client_streaming(
                self.client,
                {
                    "model": payload.model,
                    "max_completion_tokens": payload.max_completion_tokens,
                    "temperature": payload.temperature,
                    "messages": payload.messages,
                    "tools": payload.tools,
                    "stream": True,
                    "reasoning_effort": payload.reasoning_effort,
                },
            )
        else:
            return await self._request_client_non_streaming(
                self.client,
                {
                    "model": payload.model,
                    "max_completion_tokens": payload.max_completion_tokens,
                    "temperature": payload.temperature,
                    "messages": payload.messages,
                    "tools": payload.tools,
                    "reasoning_effort": payload.reasoning_effort,
                },
            )

    async def _request_client_non_streaming(
        self, openai_client: AsyncOpenAI, params: CompletionCreateParamsNonStreaming
    ) -> tuple[bool, str, ChatCompletion | None]:
        params["stream"] = False
        try:
            completion: ChatCompletion = await openai_client.chat.completions.create(
                **params, extra_body={"reasoning": {"enabled": True}}
            )
            return True, "", completion
        except AuthenticationError:
            return False, "Authentication error", None
        except RateLimitError:
            return False, "Rate limited", None
        except BadRequestError as e:
            return False, f"Malformed payload request: {e.message}", None
        except APITimeoutError:
            return False, "Request timed out", None
        except APIConnectionError:
            return (
                False,
                "Connection lost. If you are using a proxy, check your internet connection, otherwise ensure kobodlcpp is running",
                None,
            )
        except APIStatusError as e:
            return False, f"Server error ({e.status_code})", None
        except OpenAIError as e:
            return False, f"OpenAI error: {e}", None

    async def _request_client_streaming(
        self, openai_client: AsyncOpenAI, params: CompletionCreateParamsStreaming
    ) -> tuple[bool, str, AsyncStream[ChatCompletionChunk] | None]:
        params["stream"] = True
        try:
            completion: AsyncStream[
                ChatCompletionChunk
            ] = await openai_client.chat.completions.create(
                **params, extra_body={"reasoning": {"enabled": True}}
            )
            return True, "", completion
        except AuthenticationError:
            return False, "Authentication error", None
        except RateLimitError:
            return False, "Rate limited", None
        except BadRequestError as e:
            return False, f"Malformed payload request: {e.message}", None
        except APITimeoutError:
            return False, "Request timed out", None
        except APIConnectionError:
            return False, "Connection lost", None
        except APIStatusError as e:
            return False, f"Server error ({e.status_code})", None
        except OpenAIError as e:
            return False, f"OpenAI error: {e}", None

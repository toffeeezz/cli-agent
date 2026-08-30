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


async def request_client_non_streaming(
    openai_client: AsyncOpenAI, params: CompletionCreateParamsNonStreaming
) -> tuple[bool, str, ChatCompletion | None]:
    params["stream"] = False
    try:
        completion: ChatCompletion = await openai_client.chat.completions.create(
            **params
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


async def request_client_streaming(
    openai_client: AsyncOpenAI, params: CompletionCreateParamsStreaming
) -> tuple[bool, str, AsyncStream[ChatCompletionChunk] | None]:
    params["stream"] = True
    try:
        completion: AsyncStream[
            ChatCompletionChunk
        ] = await openai_client.chat.completions.create(**params)
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

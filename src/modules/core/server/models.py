from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolUnionParam
from pydantic import BaseModel

from modules.config.models import AgentConfig


class ServerPayload(BaseModel):
    messages: list[ChatCompletionMessageParam] = []
    tools: list[ChatCompletionToolUnionParam] = []
    config: AgentConfig

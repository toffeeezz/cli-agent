import json
import logging
from collections.abc import AsyncGenerator
from enum import Enum
from logging import Logger
from pathlib import Path
import re
from typing import final

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessage,
    ChatCompletionMessageFunctionToolCall,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCallUnion,
)

from ame.errors import ProgramError
from ame.llm.llm import LanguageModel, ReasoningDetail, ResponseModel
from ame.settings.settings import get_settings
from ame.tools.tool_registry import (
    ToolArgumentError,
    ToolError,
    ToolNotFoundError,
    tool_registry,
)

logger: Logger = logging.getLogger(__name__)


class Status(Enum):
    STANDBY = 0
    REPLYING = 1
    USING_TOOL = 2


@final
class Agent:
    status: Status
    llm: LanguageModel | None
    max_loops: int = 5
    messages: list[ChatCompletionMessageParam]

    def __init__(self) -> None:
        settings = get_settings()
        self.status = Status.STANDBY
        self.llm = None
        self.messages = []
        system_prompt: ChatCompletionMessageParam = {
            "role": "system",
            "content": Path(settings.llm_system_prompt).read_text(encoding="utf-8"),
        }
        self.messages.append(system_prompt)
        logger.info(f"Agent initialzed: No, of Tools ({len(tool_registry.schemas)})")

    async def execute_tools(self, tool: ChatCompletionMessageToolCallUnion) -> None:
        if not isinstance(tool, ChatCompletionMessageFunctionToolCall):
            logger.warning(
                "Skipping tool call of unsupported type: %r", type(tool).__name__
            )
            return

        tool_call_id: str = tool.id
        func = tool.function
        name: str = func.name
        kwargs_str = func.arguments

        logger.debug(
            "Tool call requested: id=%s name=%s raw_arguments=%s",
            tool_call_id,
            name,
            kwargs_str,
        )

        try:
            kwargs: dict[str, object] = json.loads(kwargs_str)
            success, tool_msg = await tool_registry.execute(name=name, kwargs=kwargs)
            content = f"The tool success status is {success}. The tool message returned: {tool_msg}"
            if success:
                logger.info("Tool '%s' executed successfully: %s", name, tool_msg)
            else:
                logger.warning("Tool '%s' reported failure: %s", name, tool_msg)
        except json.JSONDecodeError as e:
            content = f"The tool success status is False. Decoding the json response of the model failed: {e}"
            logger.error(
                "Failed to decode arguments for tool '%s': %s (raw=%s)",
                name,
                e,
                kwargs_str,
            )
        except ToolNotFoundError as e:
            content = f"{e}"
            logger.error("Tool not found: %s", e)
        except ToolArgumentError as e:
            content = str(e)
            logger.error("Invalid arguments for tool '%s': %s", name, e)
        except ToolError as e:
            content = str(e)
            logger.error("Tool '%s' raised ToolError: %s", name, e)
        except Exception as e:
            content = f"The tool success status is False. Unexpected error while executing '{name}': {e}"
            logger.exception("Unexpected error while executing tool '%s'", name)

        tool_prompt: ChatCompletionMessageParam = {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content,
        }
        self.messages.append(tool_prompt)

    async def get_reply(self, prompt: str) -> AsyncGenerator[str, None]:
        settings = get_settings()
        logger.info("New prompt sent: %r", prompt)

        self.llm = LanguageModel()

        user_prompt: ChatCompletionMessageParam = {"role": "user", "content": prompt}
        self.messages.append(user_prompt)
        max_loops = settings.max_agent_loops

        self.status = Status.REPLYING

        for iteration in range(max_loops):
            logger.debug("Agent loop iteration %d/%d", iteration + 1, max_loops)
            response = await self.get_model_response()

            if response.reasoning_details:
                reasoning_text = " ".join(
                    detail.get("text", "") for detail in response.reasoning_details
                )
                logger.debug(
                    "Reasoning (iteration %d): %s", iteration + 1, reasoning_text
                )

            match response.finish_reason:
                case "stop":
                    logger.info("Model finished with a final answer (stop).")
                    yield response.content
                    self.status = Status.STANDBY
                    return
                case "tool_calls":
                    logger.info(
                        "Model requested %d tool call(s).", len(response.tool_calls)
                    )
                    if response.content:
                        yield response.content
                    else:
                        yield f"Thinking: {response.reasoning}..."
                    self.status = Status.USING_TOOL
                    assistant_msg: ChatCompletionAssistantMessageParam = {
                        "role": "assistant",
                        "content": response.content,
                        "tool_calls": response.tool_calls,
                    }
                    self.messages.append(assistant_msg)
                    for tool in response.tool_calls:
                        await self.execute_tools(tool)
                    # loop continues — no return here, this is the only non-terminal case
                case "content_filter":
                    logger.warning("Response blocked by content filter.")
                    yield response.refusal_msg
                    return
                case "length":
                    logger.warning("Response truncated: exceeded max token length.")
                    yield "exceeded token length"
                    return
                case _:
                    logger.error(
                        "Unsupported finish_reason encountered: %r",
                        response.finish_reason,
                    )
                    yield "Mode is using function_call which is not supported"
                    return

        logger.error(
            "Exceeded max agent loop iterations (%d) without a final answer.",
            max_loops,
        )
        yield "ERROR EXCEEDED MAX ITERATIONS"

    async def get_model_response(self) -> ResponseModel:
        settings = get_settings()
        if self.llm is None:
            raise ProgramError("LanguageModel not initialzed")
        response = await self.llm.get_response(
            url=settings.api_url,
            api_key=settings.api_key,
            model=settings.llm_model,
            tools=tool_registry.schemas,
            messages=self.messages,
        )

        choices = response.choices[0]

        message: ChatCompletionMessage = choices.message
        extra = message.model_extra or {}

        content: str = message.content or ""
        refusal_msg: str = message.refusal or ""
        tool_calls: list[ChatCompletionMessageToolCallUnion] = message.tool_calls or []
        finish_reason = choices.finish_reason
        reasoning_details: list[ReasoningDetail] | None = extra.get("reasoning_details")
        reasoning: str | None = extra.get("reasoning")

        logger.debug(
            "Model response parsed: finish_reason=%s content_len=%d tool_call_count=%d",
            finish_reason,
            len(content),
            len(tool_calls),
        )

        return ResponseModel(
            content=content.strip(),
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            refusal_msg=refusal_msg,
            reasoning_details=reasoning_details or [],
            reasoning=reasoning or "",
        )


agent = Agent()

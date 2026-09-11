import datetime
import json
import logging
from collections.abc import AsyncGenerator
from pathlib import Path

from openai import AsyncOpenAI, AsyncStream
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessageFunctionToolCall,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCallUnion,
    ChatCompletionMessageToolCallUnionParam,
)
from openai.types.chat.chat_completion_chunk import (
    ChoiceDeltaToolCall,
    ChoiceDeltaToolCallFunction,
)
from openai.types.chat.chat_completion_message_tool_call import Function
from pydantic import ValidationError

from modules.config.models import AgentConfig
from modules.core.agent.models import (
    AgentError,
    AgentEvent,
    GeneratingFinished,
    GeneratingResponse,
    StreamingFinished,
    StreamingResponse,
)
from modules.core.memory.memory import MemoryManager
from modules.core.memory.models import MemorySession
from modules.core.server.models import (
    FinishReason,
    OpenRouterAssistantMessageParam,
    ReasoningDetail,
    ServerPayload,
    ServerResponse,
    ToolCall,
)
from modules.core.server.server import Server
from modules.errors import ProgramError
from modules.skill.models import ToolResult
from modules.skill.pool import SKILL_ENTRIES
from modules.skill.registry import SkillRegistry

logger = logging.getLogger(__name__)


class Agent:
    skill_registry: SkillRegistry
    _memory_manager: MemoryManager
    server: Server

    def __init__(self, config: AgentConfig) -> None:
        timestamp = datetime.datetime.now(datetime.UTC).strftime("%D")
        new_session = MemorySession(start_date=timestamp)
        client = AsyncOpenAI(base_url=config.url, api_key=config.api_key)

        self.skill_registry = SkillRegistry(SKILL_ENTRIES)
        self._memory_manager = MemoryManager(new_session)
        self.server = Server(client)

        # Initialize system prompt
        system_prompt_content = config.system_prompt_path.read_text()
        for skill_entry in self.skill_registry.skill_entries.values():
            system_prompt_content += f"\n# {skill_entry.name}\n + {skill_entry.desc}"
        system_prompt: ChatCompletionMessageParam = {
            "role": "system",
            "content": system_prompt_content,
        }

        self._memory_manager.add_message(system_prompt)
        self._memory_manager.current_session.registered_skills.extend(
            self.skill_registry.registered_skills.keys()
        )

    def load_session(self, path: str) -> None:
        logger.info(f"Loading session from: {path}")
        path: Path = Path(path)
        if not path.exists():
            logger.warning("Failed to load session: File does not exist")
            return
        try:
            session = MemorySession.model_validate_json(path.read_text())
            logger.info(f"The loaded session format was: {session}")
        except ValidationError as e:
            raise ProgramError(f"Failed to load session. Invalid format: {e}")
        self.skill_registry.registered_skills.clear()

        for skill_name in session.registered_skills:
            success, _ = self.skill_registry.register_skill(skill_name)
            logger.info(
                f"The {skill_name} skill was loaded from session with a success value of {success}."
            )

        self._memory_manager.load_session(session)

    async def save_session(self, path: str) -> None:
        await self._memory_manager.save_session(path)

    async def generate_response(
        self, name: str, prompt: str, config: AgentConfig
    ) -> AsyncGenerator[AgentEvent]:
        user_prompt: ChatCompletionMessageParam = {
            "role": "user",
            "name": name,
            "content": f"[{name}]: {prompt.strip()}",
        }
        self._memory_manager.add_message(user_prompt)
        loop_count: int = 1
        while loop_count <= config.max_loops:
            loop_count += 1

            payload = ServerPayload(
                model=config.model,
                max_completion_tokens=config.max_completion_tokens,
                temperature=config.temperature,
                messages=self._memory_manager.messages,
                tools=self.skill_registry.tool_schemas,
                reasoning_effort=config.reasoning_effort,
            )
            yield GeneratingResponse()
            success, error_msg, response = await self.server.send_request(
                payload=payload, stream=config.stream
            )

            if not success or response is None:
                raise AgentError(
                    f"Failed to get a response from the server due to cause: {error_msg}"
                )

            if isinstance(response, ChatCompletion):
                server_response = await self._build_non_streaming_response(response)
                yield GeneratingFinished(
                    content=server_response.content,
                    reasoning=server_response.reasoning or "",
                )
            else:
                final_response: ServerResponse | None = None
                async for stream in self._build_streaming_response(response):
                    if isinstance(stream, StreamingResponse):
                        yield stream
                    else:
                        final_response = stream
                        yield StreamingFinished(
                            content=stream.content, reasoning=stream.reasoning
                        )
                if final_response is None:
                    raise AgentError("Streaming ended without a final response")
                server_response = final_response

            logger.info(f"Agent: {server_response.content}")
            logger.info(f"Agent[Reasoning]: {server_response.reasoning}")

            assitant_msg: OpenRouterAssistantMessageParam = {
                "role": "assistant",
                "content": server_response.content.strip(),
                "reasoning_details": server_response.reasoning_details,
                "reasoning": server_response.reasoning,
            }
            if server_response.message:
                self._memory_manager.add_message(assitant_msg)

            match server_response.finish_reason:
                case FinishReason.STOP:
                    return
                case FinishReason.TOOL_CALLS:
                    await self._use_skill(tool_calls=server_response.tool_calls)
                    continue
                case FinishReason.LENGTH:
                    raise AgentError(
                        "The response exceeded max completion token length"
                    )
                case _:
                    # Temporary handling of both cases
                    raise AgentError(
                        "The response was either filtered or the response ended with a function call"
                    )

        raise AgentError(f"Agent exceeded max iterations: {loop_count}")

    async def _use_skill(
        self, tool_calls: list[ChatCompletionMessageToolCallUnion]
    ) -> None:
        tool_results = await self._execute_tool(tool_calls)

        for id, result in tool_results.items():
            tool_prompt: ChatCompletionMessageParam = {
                "role": "tool",
                "tool_call_id": id,
                "content": f"{result.name} tool from {result.skill_name} returned a success value of {result.success}: {result.value}",
            }
            logger.info(
                f"The agent used the following tool from {result.skill_name.capitalize()} skill: {result.name}\nSuccess: {result.success}"
            )
            self._memory_manager.add_message(tool_prompt)

    async def _execute_tool(
        self, tool_calls: list[ChatCompletionMessageToolCallUnion]
    ) -> dict[str, ToolResult]:
        tool_results: dict[str, ToolResult] = {}
        for tc in tool_calls:
            if not isinstance(tc, ChatCompletionMessageFunctionToolCall):
                continue
            if tc.type != "function":
                continue

            try:
                logger.info(
                    f"The agent is attempting to use {tc.function.name} tool with args: {tc.function.arguments}"
                )
                kwargs = json.loads(tc.function.arguments)
                result = await self.skill_registry.execute_skill(
                    tc.function.name, kwargs
                )
                if tc.function.name.strip() == "core.register_skill":
                    self._memory_manager.current_session.registered_skills.append(
                        kwargs.get("name") or ""
                    )
            except json.JSONDecodeError as e:
                logger.error(
                    f"Model returned an invalid json format for the tool arguments: {e}"
                )
                continue
            tool_results[tc.id] = result

        return tool_results

    async def _build_non_streaming_response(
        self, response: ChatCompletion
    ) -> ServerResponse:
        choices = response.choices[0]
        message = choices.message
        content = message.content or ""
        finish_reason = choices.finish_reason
        tool_calls = message.tool_calls or []
        extra = message.model_extra or {}
        reasoning = extra.get("reasoning")
        reasoning_details = extra.get("reasoning_details")

        assistant_msg: OpenRouterAssistantMessageParam = {
            "role": "assistant",
            "content": content,
            "reasoning": reasoning or "",
            "reasoning_details": reasoning_details or [],
        }

        return ServerResponse(
            message=assistant_msg,
            content=content,
            reasoning_details=reasoning_details or [],
            reasoning=reasoning or "",
            tool_calls=tool_calls,
            finish_reason=FinishReason(finish_reason),
        )

    async def _build_streaming_response(
        self, chunks: AsyncStream[ChatCompletionChunk]
    ) -> AsyncGenerator[ServerResponse | StreamingResponse, None]:
        server_response = ServerResponse()

        accumulated_reasoning_details: list[ReasoningDetail] = []
        accumulated_tool_calls: dict[int, ToolCall] = {}

        # Builds the server_response from the streaming chunks
        async for tc in chunks:
            choices = tc.choices[0]
            delta_content = choices.delta.content
            delta_reasoning = getattr(choices.delta, "reasoning", None)
            delta_reasoning_details: list[dict[str, object]] | None = getattr(
                choices.delta, "reasoning_details", None
            )
            delta_tool_calls: list[ChoiceDeltaToolCall] | None = (
                choices.delta.tool_calls
            )

            if delta_reasoning and isinstance(delta_reasoning, str):
                server_response.reasoning += delta_reasoning
            if delta_content:
                server_response.content += delta_content

            if delta_reasoning_details:
                self._parse_reasoning_details(
                    delta_reasoning_details, accumulated_reasoning_details
                )

            if choices.finish_reason:
                server_response.finish_reason = FinishReason(choices.finish_reason)

            if delta_tool_calls:
                self._parse_tool_calls(delta_tool_calls, accumulated_tool_calls)

            yield StreamingResponse(
                delta_content=delta_content, delta_reasoning=delta_reasoning
            )

        tool_calls_param: list[ChatCompletionMessageToolCallUnionParam] = []
        tool_calls: list[ChatCompletionMessageToolCallUnion] = []
        for tc in accumulated_tool_calls.values():
            tool_call_param: ChatCompletionMessageToolCallUnionParam = {
                "id": tc["id"],
                "type": "function",
                "function": {
                    "name": tc["name"],
                    "arguments": tc["params"],
                },
            }
            tool_call = ChatCompletionMessageFunctionToolCall(
                id=tc["id"],
                type="function",
                function=Function(name=tc["name"], arguments=tc["params"]),
            )
            tool_calls.append(tool_call)
            tool_calls_param.append(tool_call_param)

        assistant_msg: OpenRouterAssistantMessageParam = {
            "role": "assistant",
            "content": server_response.content,
            "reasoning": server_response.reasoning,
            "reasoning_details": server_response.reasoning_details,
            "tool_calls": tool_calls_param,
        }

        server_response.message = assistant_msg
        server_response.tool_calls = tool_calls
        yield server_response

    def _parse_tool_calls(
        self,
        delta_tool_calls: list[ChoiceDeltaToolCall],
        tool_call_list: dict[int, ToolCall],
    ) -> None:
        for delta_tc in delta_tool_calls:
            function: ChoiceDeltaToolCallFunction | None = delta_tc.function
            tool_call = tool_call_list.setdefault(
                delta_tc.index, ToolCall(id="", name="", params="")
            )

            if delta_tc.id:
                tool_call["id"] = delta_tc.id
            if function:
                if function.arguments:
                    tool_call["params"] += function.arguments
                if function.name:
                    tool_call["name"] += function.name

    def _parse_reasoning_details(
        self,
        delta_rd_list: list[dict[str, object]],
        reasoning_detail_list: list[ReasoningDetail],
    ) -> None:
        for delta_rd in delta_rd_list:
            try:
                rd = ReasoningDetail.model_validate(delta_rd)
                reasoning_detail_list.append(rd)
            except ValidationError as e:
                logger.error(f"The model streamed an unexepcted dict format: {e}")

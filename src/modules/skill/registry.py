import asyncio
import functools
import inspect
import logging
from collections.abc import Callable

from openai.types.chat import ChatCompletionToolUnionParam

from modules.skill.models import Skill, SkillEntry, Tool, ToolResult

logger = logging.getLogger("Skill Registry")


class SkillRegistry:
    skill_entries: dict[str, SkillEntry]
    registered_skills: dict[str, Skill]

    def __init__(self, entries: dict[str, SkillEntry]) -> None:
        self.skill_entries = entries
        self.registered_skills = {
            "core": Skill(
                name="core",
                instructions="Use this skill to register skills to use the tools of that skill",
                tool_names=["register_skill"],
                tool_list={
                    "register_skill": Tool(
                        name="core.register_skill",
                        tool_func=self.register_skill,
                        tool_schema={
                            "type": "function",
                            "function": {
                                "name": "core.register_skill",
                                "description": (self.register_skill.__doc__ or ""),
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                            "description": (
                                                "The exact skill name as shown in the skill "
                                                "catalog (case-sensitive). Only use names you've "
                                                "actually seen listed — do not guess."
                                            ),
                                        },
                                    },
                                    "required": ["name"],
                                },
                            },
                        },
                    )
                },
            )
        }

        if not self.skill_entries:
            logger.warning(
                "The skill entry list is empty. Skill Pool may not have been loaded"
            )

    def register_skill(self, name: str) -> tuple[bool, str]:
        """Register a skill by name, loading its tools so you can call them.

        Call this before attempting to use any tool belonging to a skill you
        haven't registered yet — you cannot call a skill's tools until its
        skill has been registered first. If you're unsure whether a skill is
        already registered, just call this; registering an already-registered
        skill is safe and simply confirms it's ready.

        Args:
            name: The exact skill name as shown in the skill catalog (case-sensitive).
                Do not guess at a name — only use names you've actually seen listed.

        Returns:
            A short status message. If registration failed, the message will
            explain why (e.g. the skill name wasn't found) — read it before
            retrying, and do not retry with the same unknown name.
        """
        if name in self.registered_skills:
            return True, f"{name} skill is already registered"
        entry = self.skill_entries.get(name)
        if entry is None:
            logger.warning(f"Tried to register an unknown skill: {name}")
            return (
                False,
                f"{name} skill could not be found in the skill pool. It may not be installed",
            )
        self.registered_skills[name] = entry.skill
        logger.debug(f"{name} skill has been registered")
        return (
            True,
            f"{name} skill has been successfully registered. Here are its instructions: {entry.skill.instructions}",
        )

    def unregister_skill(self, name: str) -> tuple[bool, str]:

        skill = self.registered_skills.get(name)

        if name not in self.registered_skills or skill is None:
            logger.warning(
                f"{name} tried to unregister a skill that is not in the registered list"
            )
            return True, f"{name} skill is already not registered"

        _ = self.registered_skills.pop(name)
        logger.debug(f"{name} skill has been unregistered")
        return True, f"{name} skill has been unregistered"

    async def execute_skill(
        self, tool_fullname: str, kwargs: dict[str, object]
    ) -> ToolResult:
        split = tool_fullname.split(".", maxsplit=1)
        try:
            skill_name = split[0]
            tool_name = split[1]
        except IndexError:
            logger.error(
                f"Tried to execute a tool with an invalid name format: {tool_fullname} "
            )
            return ToolResult(
                skill_name="",
                success=False,
                value="Failed to parse the name for the tool. Format should be: 'skillname.toolname'",
            )

        skill = self.registered_skills.get(skill_name)

        if skill is None:
            logger.warning(
                f"Tried to execute a tool from an unregistered skill: {skill_name}"
            )
            return ToolResult(
                skill_name=skill_name,
                success=False,
                value=f"{skill_name} skill is not yet registered. Unable to execute a tool from it",
            )

        tool = skill.tool_list.get(tool_name)

        if tool_name not in skill.tool_names or tool is None:
            logger.warning(
                f"Tried to execute an unknown tool from {skill_name}: {tool_name}"
            )
            return ToolResult(
                name=tool_name,
                skill_name=skill_name,
                success=False,
                value=f"{tool_name} tool cound not be found in {skill_name} skill",
            )

        missing_args = self._get_missing_args(tool.tool_func, kwargs)
        if len(missing_args) > 0:
            logger.warning(
                f"Tried to execute {tool_name} tool from {skill_name} skill with missing arguments: {missing_args}"
            )
            return ToolResult(
                name=tool_name,
                skill_name=skill_name,
                success=False,
                value=f"Failed to execute {tool_name} tool from {skill_name} skill: Missing arguments {missing_args}",
            )

        if inspect.iscoroutinefunction(tool.tool_func):
            result = await tool.tool_func(**kwargs)
        else:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None, functools.partial(tool.tool_func, **kwargs)
            )

        succ, msg = result
        logger.info(f"{tool_name} tool from {skill_name} skill was executed")

        return ToolResult(
            name=tool_name, skill_name=skill_name, success=succ, value=msg
        )

    def _get_missing_args(
        self, func: Callable[..., tuple[bool, object]], kwargs: dict[str, object]
    ) -> list[str]:
        sig = inspect.signature(func)
        missing_args: list[str] = []

        for name, param in sig.parameters.items():
            if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                continue

            if param.default is inspect.Parameter.empty and name not in kwargs:
                missing_args.append(name)
        return missing_args

    @property
    def tool_schemas(self) -> list[ChatCompletionToolUnionParam]:
        schemas: list[ChatCompletionToolUnionParam] = []
        for skill in self.registered_skills.values():
            schemas.extend(v.tool_schema for v in skill.tool_list.values())
        return schemas

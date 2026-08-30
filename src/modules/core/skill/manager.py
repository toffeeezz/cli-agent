from typing import final

from openai.types.chat import ChatCompletionToolUnionParam

from modules.skills.errors import SKillNotFoundError
from modules.skills.loader import (
    EXTERNAL_SKILLS_DIR,
    INTERNAL_SKILLS_DIR,
    build_skills,
    get_skill,
    load_skill_metadatas,
)
from modules.skills.models import Skill
from modules.skills.registry import ToolRegistry

_internal_skills_metadatas = load_skill_metadatas(INTERNAL_SKILLS_DIR)
_external_skills_metadatas = load_skill_metadatas(EXTERNAL_SKILLS_DIR)

_internal_skills = build_skills(_internal_skills_metadatas)
_external_skills = build_skills(_external_skills_metadatas)

loaded_skills = _internal_skills | _external_skills


@final
class SkillRegistry:
    def __init__(self) -> None:
        self.tool_registry = ToolRegistry()
        self.active_skills: dict[str, Skill] = {}
        _ = self.tool_registry.register("core", self.load_skill)

    async def load_skill(self, name: str) -> tuple[bool, str]:
        """Activates a skill by name, making its tools available for the model to call.

        Looks up `name` in the full skill catalog (`loaded_skills`) and, if found,
        adds it to `active_skills` so its tool schemas get included in the next
        API call's `tools` param. No-ops if the skill is already active.

        Args:
            name: The skill's registered name, as it appears in `loaded_skills`
                (i.e. the `name` field from that skill's SKILL.md frontmatter).

        Returns:
            A `(success, message)` tuple:
                - `(False, ...)` if the skill is already loaded, or if no skill
                matches `name` (see `SkillNotFoundError`).
                - `(True, ...)` if the skill was newly activated.
            `message` is a human-readable status string, not meant for parsing —
            it's surfaced back to the model as the tool result.
        """
        if name in self.active_skills:
            return True, f"Skill {name} is already loaded"
        try:
            skill = get_skill(loaded_skills, name)
        except SKillNotFoundError as e:
            return False, e.message
        self.active_skills[name] = skill
        for func in skill.tools:
            _ = self.tool_registry.register(name, func)
        return True, f"Skill {name} successfully loaded"

    def unload_skill(self, name: str) -> tuple[bool, str]:
        if name not in self.active_skills:
            return True, f"Skill {name} is already not loaded"
        del self.active_skills[name]
        self.tool_registry.unregister(name)
        return True, f"Skill {name} is successfully unloaded"

    @property
    def schema(self) -> list[ChatCompletionToolUnionParam]:
        return self.tool_registry.schema

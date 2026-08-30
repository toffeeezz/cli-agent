import asyncio

from modules.core.errors import ProgramError
from modules.core.skill.manager import SkillRegistry
from modules.skills.loader import (
    INTERNAL_SKILLS_DIR,
    build_skills,
    get_skill,
    load_skill_metadatas,
)

metadatas = load_skill_metadatas(INTERNAL_SKILLS_DIR)
skills = build_skills(metadatas)

skill = get_skill(skills, "file_system_operations")

registry = SkillRegistry()

try:
    succ, msg = asyncio.run(registry.load_skill("git_operations"))
    succ, msg = registry.unload_skill("git_operations")
    print(msg)
    print(registry.schema)
except ProgramError as e:
    print(e)

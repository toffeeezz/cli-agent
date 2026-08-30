import importlib.util
import inspect
from collections.abc import Callable
from pathlib import Path

import frontmatter
from pydantic import ValidationError
from yaml import YAMLError

from modules.core.errors import ProgramError
from modules.skills.base import (
    Skill,
    SkillData,
    SkillInvalidMD,
    SkillMissingMD,
    SkillModuleError,
    ToolRegistry,
)

INTERNAL_SKILLS_DIR = Path(__file__).resolve().parent
EXTERNAL_SKILLS_DIR = Path(__file__).resolve().parent.parent.parent / "plugins/skills"


def load_skill_metadatas(dir: Path) -> list[SkillData]:
    internal_skill_metadatas: list[SkillData] = []
    try:
        for skill_entry in dir.iterdir():
            if skill_entry.is_dir() and not skill_entry.name.startswith("_"):
                try:
                    post = frontmatter.load(Path(skill_entry / "SKILL.md"))
                    post.metadata["path"] = Path(skill_entry / "tools.py")
                    skill: SkillData = SkillData.model_validate(post.metadata)
                    internal_skill_metadatas.append(skill)
                except FileNotFoundError:
                    raise SkillMissingMD(skill_entry)
                except YAMLError as e:
                    raise SkillInvalidMD(skill_entry, str(e)) from e
                except ValidationError as e:
                    raise SkillInvalidMD(skill_entry, str(e)) from e
    except FileNotFoundError:
        raise ProgramError(
            f"The path for external skill plugins could not be found: {dir}"
        )
    return internal_skill_metadatas


def build_sklls(metadatas: list[SkillData]) -> list[Skill]:
    skills: list[Skill] = []
    for data in metadatas:
        if not data.path.is_file() or data.path.suffix != ".py":
            raise SkillModuleError(
                f"Invalid Python file or path does not exist: {data.path}"
            )
        module_name = data.path.stem

        spec = importlib.util.spec_from_file_location(module_name, data.path)
        if spec is None or spec.loader is None:
            raise SkillModuleError(f"Failed to create module spec for: {data.path}")

        module = importlib.util.module_from_spec(spec)
        loader = spec.loader
        loader.exec_module(module)
        registry = ToolRegistry()
        members = inspect.getmembers(module, predicate=inspect.isfunction)
        if len(members) <= 0:
            raise SkillModuleError(
                f"Module does not contain any functions: {module_name}"
            )
        for member in members:
            func: Callable[..., object]
            func = member[1]
            _ = registry.register(data.name, func)

        skills.append(Skill(name=data.name, tool_registry=registry))

    return skills

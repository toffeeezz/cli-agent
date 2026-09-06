import importlib.util
import inspect
import logging
from collections.abc import Callable
from pathlib import Path
from typing import get_type_hints

import frontmatter
import yaml
from pydantic import TypeAdapter, ValidationError

from modules.skill.errors import SkillBuilderError
from modules.skill.models import Skill, SKillData, SkillEntry, Tool

SKILLS_PATH = Path(__file__).resolve().parent

SKILL_ENTRIES: dict[str, SkillEntry] = {}
EXCLUDED_DIRS: list[str] = ["__pycache__"]

logger = logging.getLogger(__name__)


def load_skill_pool() -> None:
    if SKILL_ENTRIES:
        return
    for path in SKILLS_PATH.iterdir():
        if not path.is_dir() or path.stem in EXCLUDED_DIRS:
            continue

        skill_md = path / "SKILL.md"
        tool_py = path / "tools.py"
        try:
            post = frontmatter.load(skill_md, encoding="utf-8")

            data = SKillData.model_validate(post.metadata)
            _build_skill_entry(data.name, post.content, data.desc, data.tools, tool_py)

            logger.info(f"{post.get('name')} skill loaded successfully")
        except FileNotFoundError:
            raise SkillBuilderError(f"Failed to load skill at {path}: MISSING SKILL.md")
        except yaml.YAMLError as e:
            raise SkillBuilderError(f"Failed to load skill at {path}: \n{e}") from e
        except ValidationError as e:
            raise SkillBuilderError(f"Failed to load skill at {path}: \n{e}") from e


def _build_skill_entry(
    name: str, content: str, desc: str, tools: list[str], tool_py: Path
) -> None:
    tool_desc = f"Skill tools: {tools}"
    desc += f"\n{tool_desc}"

    if not tool_py.is_file():
        raise SkillBuilderError(f"Missing tools.py for skill '{name}' at {tool_py}")

    spec = importlib.util.spec_from_file_location(tool_py.stem, tool_py)

    if spec is None or spec.loader is None:
        raise SkillBuilderError(f"Failed to create spec from {tool_py}")

    module = importlib.util.module_from_spec(spec)

    loader = spec.loader
    loader.exec_module(module)

    members = inspect.getmembers(module, predicate=inspect.isfunction)
    local_functions: list[Callable[..., tuple[bool, object]]] = []

    if len(members) <= 0:
        raise SkillBuilderError(f"The module {tool_py} does not contain any functions")

    for _, func in members:
        if func.__module__ != module.__name__:
            continue

        if not func.__doc__ or func.__doc__ == "":
            logger.warning(
                f"The function {func.__name__} does not have a docstring which reduces the agent's efficieny to use this tool"
            )
        local_functions.append(func)

    if len(local_functions) <= 0:
        raise SkillBuilderError(
            f"The module {tool_py} does not contain any local_functions"
        )

    tool_schema = _build_tool_schema(name, local_functions)
    skill = Skill(
        name=name, instructions=content, tool_list=tool_schema, tool_names=tools
    )
    skill_entry = SkillEntry(name=skill.name, desc=desc, skill=skill)
    SKILL_ENTRIES[name] = skill_entry


def _build_tool_schema(
    namespace: str, local_functions: list[Callable[..., tuple[bool, object]]]
) -> dict[str, Tool]:
    tool_list: list[Tool] = []
    tool: dict[str, Tool] = {}
    for func in local_functions:
        sig = inspect.signature(func)
        hints = get_type_hints(func)

        properties: dict[str, object] = {}
        required: list[str] = []

        for name, param in sig.parameters.items():
            if name == "self":
                continue
            param_type = hints.get(name, str)
            properties[name] = TypeAdapter(param_type).json_schema()

            if param.default is inspect.Parameter.empty:
                required.append(name)

        tool_name = f"{namespace}.{func.__name__}"

        tool_schema: Tool = Tool(
            name=tool_name,
            tool_func=func,
            tool_schema={
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": func.__doc__ or "",
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                    },
                },
            },
        )
        tool[func.__name__] = tool_schema
        tool_list.append(tool_schema)
    return tool

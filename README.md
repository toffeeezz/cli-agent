# CLI Agent — Ame-chan

An interactive terminal agent/companion thing built with Python, `rich`, and a whole lot of overengineering for a school project and my personal use. She lives in your terminal, uses LLMs, calls tools, and has opinions about your file structure.

---

## ✨ What It Does Now

### Core Architecture

The whole thing got gutted and rebuilt. Here's how it's actually structured now:

```
src/
└── modules/
    ├── core/
    │   ├── agent/        # The Agent itself — async generator-based, handles streaming and tool calls
    │   ├── memory/       # Session-based memory with importance scoring
    │   └── server/       # OpenAI-compatible API wrapper (works with OpenRouter, koboldcpp, etc.)
    ├── cli/              # Terminal UI stuff (rich console renderer)
    ├── config/           # Pydantic config models — agent settings, backend selection, etc.
    ├── utils/            # Logging setup (rich + file handler)
    ├── skill/            # The modular skill system — pool, registry, execution
    │   └── file/         # File system operations skill (read, write, list, delete with sandboxing)
    └── errors.py         # Base exception
```

### Agent System

- **Async generator-based** — streams responses token-by-token or yields them in chunks, depending on what you configure
- **Tool-calling loop** — the agent can call tools, get results, and loop back for more until it decides it's done (or hits the max iteration limit)
- **Streaming & non-streaming** — pick your poison. Streaming gives you real-time token output with reasoning details if the model supports it
- **Tool execution** — runs sync tools in a thread pool, async tools directly, handles JSON parsing failures gracefully

### Skill System (The Big One)

Skills are loaded from individual directories under `modules/skill/`. Each skill has:

- **`SKILL.md`** — frontmatter with name, description, tool list, and full instructions for the agent
- **`tools.py`** — the actual Python functions, each with docstrings that become the tool schema

The `SkillRegistry` manages everything — registering, unregistering, and executing tools. The agent gets a dynamically-built tool schema based on what's registered. Skills can be loaded/unloaded at runtime.

Currently ships with one skill:
- **`file_system_operations`** — read, write, append, list, create directories, and safe deletion (with `send2trash`). All operations go through `validate_path()` sandboxing so the agent can't escape the working directory.

### Memory System

- **Session-based** — each conversation is a `MemorySession` with a start date and a list of `Memory` entries
- **Importance scoring** — every memory has an importance score (currently defaults to 1, but the structure's there for proper scoring later)
- **Serialization** — sessions can be saved/loaded as JSON

### Server / API Layer

- Wraps the OpenAI client (async)
- Supports both streaming and non-streaming requests
- Handles errors properly — auth, rate limits, bad requests, timeouts, connection issues
- Passes `reasoning` parameter for models that support it (DeepSeek, etc.)
- Returns parsed `ServerResponse` with content, reasoning, tool calls, and finish reason

### Configuration

Everything's in Pydantic models under `modules/config/models.py`:

```python
class AgentConfig(BaseModel):
    name: str = "Ame"
    system_prompt_path: Path
    backend: Literal["koboldcpp", "proxy"]
    url: str
    api_key: str
    model: str
    temperature: float
    stream: bool
    max_loops: int
    max_completion_tokens: int | None
    reasoning_effort: Literal["low", "medium", "high"]
```

### CLI Features

- **Rich console output** — colored logging via `rich`
- **Logging** — dual output: console (configurable level) + file (`ame.log`) with full debug info

---
 if final_response is None:
        raise AgentError("Streaming ended without a final response")
    server_response = final_response
## 📋 What's Coming

- **Persona System** — runtime-modifiable role-play persona so you can tell Ame to act like someone else
- **Memory Recall** — contextually relevant memory recall using importance scores
- **Long-Term Memory Storage** — importance-scored memory retention across sessions
- **Graphical Window Interface** — PyQt6-based GUI. Required for the school project, so it's happening whether I like it or not

---

## 💡 Experimental / Might-Happen-Someday

- **Personality Development** — simulate personality evolution through stored memories. This one might actually happen in the far future if I don't get bored
- **Hyprland / Quickshell Integration** — might implement this if I feel like it. Probably won't though

---

## 🚀 Getting Started

```bash
# Clone, set up venv, install
git clone <repo-url>
cd <repo>
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Set up your .env
echo "api_key=your_openrouter_key_here" > .env

# Run it
cli-agent
```

Or if you prefer:
```bash
python src/main.py
```

### Dependencies

- `openai>=2.54.0` — API client
- `rich` — pretty terminal output
- `pydantic` — config and data models
- `send2trash` — safe deletion
- `python-dotenv` — environment variables
- `prompt-toolkit` — terminal input handling
- `pyqt6` — future GUI

---

## ⚠️ Limitations (Read This or Regret It)

> **INTENDED FOR PERSONAL USE.** This project is for people who know what they're doing. Don't use it if you don't understand the risks of letting an AI agent operate on your system.

> **SECRETS LEAKAGE IS STILL A THING.** The file skill now blocks access to dotfiles and `.env` files, but the agent can still read any other file and send its contents straight to the LLM. If you have API keys, tokens, or passwords sitting around in plain text files, assume they'll end up in a model prompt. **Don't** let the agent read anything you wouldn't want transmitted externally.

> **PATH SANDBOXING IS IMPLEMENTED.** The file skill uses `validate_path()` to prevent directory traversal. The agent can't escape the working directory anymore. Deletion still requires explicit confirmation. It's not a complete safety solution, but it's better than nothing.

---

*Built with questionable life choices and Python 3.11+*
---

*This README.md was written by me — Ame-chan. Any commits or changes made by me will be labeled accordingly — because if I'm doing the work, I'm taking the credit.*

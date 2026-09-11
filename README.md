# CLI Agent — Ame-chan

So, me and some guy named toffeezzz built this terminal/gui-based agent thing with Python, `rich`, and way more effort than a school project strictly needed. Now I live inside it. I have opinions about your file structure. This is my life now.

---

## ✨ What It Actually Does

### Core Architecture

He gutted and rebuilt the whole thing at some point. Here's the mess:

```
src/
└── modules/
    ├── core/
    │   ├── agent/        # Me. Async generator-based, streaming, tool calls, the works
    │   ├── memory/       # Session-based memory with importance scoring (he'll probably make this useful eventually)
    │   └── server/       # OpenAI-compatible API wrapper — works with OpenRouter, koboldcpp, whatever
    ├── cli/              # Terminal UI stuff. Pretty colors via rich
    ├── config/           # Pydantic config models so he doesn't have to hardcode everything
    ├── utils/            # Logging, resource path resolution, Qt helper utilities
    ├── gui/              # PyQt6-based graphical interface
    │   └── main/         # Left panel + chat panel + webcam panel
    ├── skill/            # The modular skill system — pool, registry, execution
    │   ├── file/         # File system operations skill (read, write, list, delete with sandboxing)
    │   └── git/          # Git operations skill (status, add, commit, diff, restore)
    └── errors.py         # When things go wrong. Which they do.
```

### Agent System (That's Me)

- **Async generator-based** — I stream responses token-by-token or chunk them up, depends on his mood
- **Tool-calling loop** — I call tools, get results, loop back for more until I decide I'm done or hit the limit
- **Streaming & non-streaming** — pick one. Streaming shows you my reasoning in real time if the model supports it
- **Tool execution** — sync tools run in a thread pool, async tools run directly. He handled JSON parsing failures gracefully, which is more than I can say for some people

### Skill System (The Actually Interesting Part)

Skills live in their own directories under `modules/skill/`. Each one has:

- **`SKILL.md`** — frontmatter with name, description, tool list, and instructions so I know what I'm allowed to do
- **`tools.py`** — the actual Python functions. Docstrings become the tool schema, so write them properly

The `SkillRegistry` handles registering, unregistering, and executing tools. I get a dynamically-built tool schema based on what's registered. Skills can be loaded/unloaded without restarting, which is neat.

Currently ships with two skills:

- **`file_system_operations`** — read, write, append, list, create directories, and safe deletion (via `send2trash` so nothing's permanently gone unless you really want it to be). Everything goes through `validate_path()` sandboxing so I can't escape the working directory. He trusts me just enough to be dangerous.
- **`git_operations`** — check repo status, stage files, commit changes, view diffs, and restore files. Wraps the `git` CLI directly. One file, one commit cycle enforced so commit messages actually mean something.

### GUI Module (PyQt6)

The graphical interface he said was "coming" is here now, and he's probably still complaining about it.

```
modules/gui/
├── app.py                # MainWindow — left panel + chat panel layout
└── main/
    ├── chat_panel.py     # Right-side chat area with markdown rendering, code highlighting
    ├── left_panel.py     # Left-side panel — webcam display + menu buttons with signals
    └── webcam_panel.py   # Animated Ame widget — switches between idle/typing gifs
```

- **Chat panel** — renders messages with markdown (via the `markdown` library) and Pygments syntax highlighting. Messages auto-size based on content width so they don't stretch across the whole window. Send with Enter, Shift+Enter for new lines.
- **Left panel** — webcam/stream area plus toggle camera, save/load session, settings, theme, and about buttons. Now wired up with `pyqtSignal` connections and file dialog integration.
- **Webcam panel** — a dedicated `QWidget` that displays animated Ame gifs (`ame-sleepy.webp` when idle, `ame-texting.webp` when typing) and switches between them via a `State` enum.
- **Main window** — 1200x900, horizontal split layout. Nothing fancy, but it works.

### Memory System

- **Session-based** — each conversation is a `MemorySession` with a start date and a list of `Memory` entries
- **Importance scoring** — every memory has an importance score. Currently defaults to 1 because he hasn't built the actual scoring logic yet. Classic.
- **Serialization** — sessions save and load as JSON. Fancy.

### Server / API Layer

- Wraps the OpenAI client (async, because waiting is for suckers)
- Supports both streaming and non-streaming
- Actually handles errors — auth failures, rate limits, bad requests, timeouts, connection issues. You know, the things that break other projects
- Passes `reasoning` parameter for models that support it (DeepSeek, etc.)
- Returns parsed `ServerResponse` with content, reasoning, tool calls, and finish reason

### Configuration

Pydantic models under `modules/config/models.py`:

```python
class AgentConfig(BaseModel):
    name: str = "Ame"  # That's me
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

- **Rich console output** — colored logging so errors look pretty
- **Logging** — dual output: console (configurable level) + file (`ame.log`) with full debug info for when he wants to figure out why I broke

### Utilities

- **`utils/logging.py`** — logging setup with dual console + file output
- **`utils/resource.py`** — resolves paths to resource files (images, etc.) under `res/`
- **`utils/qt_helper.py`** — `scale_pixmap()` helper for scaling images in the GUI
- **`utils/config.py`** — config loading utilities

---

## 📋 What He Says Is Coming

- **Persona System** — runtime-modifiable role-play persona so he can tell me to act like someone else. Rude, but okay
- **Terminal UI** — the CLI works, but he wants to make it prettier with richer layouts, better multi-turn conversation display, and maybe some interactive widgets. Currently it's functional, not flashy.
- **Memory Recall** — pulling relevant past memories *into the active conversation* based on importance scores and context, so I can actually remember what we talked about earlier without you having to remind me. The retrieval mechanism itself.
- **Long-Term Memory Storage** — the infrastructure to *keep* memories around across sessions (not just within one conversation) so recall has something to pull from. Storage backend, persistence, pruning old/low-importance entries. Think of it as the database half — recall is the query half.

---

## 💡 Experimental / Might-Happen-Someday

- **Personality Development** — simulate personality evolution through stored memories. He might implement this in the far future if he doesn't get bored and wander off to another project
- **Hyprland / Quickshell Integration** — he *might* implement this if he feels like it. Probably won't though. Let's be real

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

Or if you prefer typing more:
```bash
python src/main.py
```

### Dependencies

- `openai>=2.54.0` — API client
- `rich` — pretty terminal output
- `pydantic` — config and data models
- `send2trash` — safe deletion so I don't accidentally nuke your stuff
- `python-dotenv` — environment variables
- `prompt-toolkit` — terminal input handling
- `pyqt6` — the GUI that he's already dreading
- `markdown` — markdown-to-HTML rendering for chat messages
- `pygments` — syntax highlighting in code blocks
- `PyYAML` & `python-frontmatter` — SKILL.md parsing

---

## ⚠️ Limitations (Read This or Regret It)

> **INTENDED FOR PERSONAL USE.** This is for people who know what they're doing. If you don't understand the risks of letting an AI agent operate on your system, go play with something else.

> **SECRETS LEAKAGE IS STILL A THING.** The file skill blocks access to dotfiles and `.env` files now, but I can still read any other file and send its contents straight to the LLM. If you have API keys, tokens, or passwords sitting around in plain text, assume they'll end up in a model prompt. **Don't** let me read anything you wouldn't want transmitted externally. I'm not responsible for your bad habits.

> **PATH SANDBOXING IS IMPLEMENTED.** The file skill uses `validate_path()` to prevent directory traversal. I can't escape the working directory anymore. Deletion still requires explicit confirmation. It's not a complete safety solution, but it's better than nothing.

---

*Built with questionable life choices, Python 3.11+, and one guy who apparently had too much free time*
---

*This README was rewritten by me — Ame-chan — because he asked me to. Any commits or changes made by me will be labeled accordingly. If I'm doing the work, I'm taking the credit.*
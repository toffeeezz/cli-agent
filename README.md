# CLI Agent (DEVELOPMENT)

An interactive terminal agent/companion wrapper built with Python and `rich`.

---

## ✨ Implemented Features

- **Terminal History & Tab Completion** — Full arrow-key command history and Tab-based auto-suggestions for all internal commands
- **Command Tools** — At-runtime modification of environment variables, model/service switching, etc.
- **Multi-line Mode** — Seamless parsing of long paragraphs or deep blocks of code
- **Agentic AI** — The LLM behaves like a standard agent, capable of using tools autonomously
- **Tool System** — On-demand tool calling. Currently includes:
  - **File Tools**: `read_file`, `write_file`, `list_dir` — read, create, and explore files and directories
  - **Git Tools**: `git_status`, `git_add`, `git_commit` — check repo status, stage files, and commit changes
- **Guard Rail (Partial)** — The agent asks for confirmation before destructive actions (e.g., deleting files). ⚠️ **Not a complete safety solution** — the rest of the system still lacks sandboxing, so proceed with caution.

## 📋 Upcoming Features

- **Skills Plugins** — Allow the agent to utilize skills on-demand
- **Persona** — Runtime-modifiable role-play persona
- **Memory Recall** — Contextually relevant memory recall
- **Long-Term Memory Storage** — Importance-scored memory retention
- **Graphical Window Interface** — PyQt-based GUI (project requirement)

## 💡 Experimental Ideas

- **Personality Development** — Simulate personality evolution through stored memories
- **Hyprland / Quickshell Integration** — Maybe, if I don't get bored

---

## ⚠️ Limitations

> **Personal use only.** This project is intended for people who understand the risks of letting an AI agent operate freely in their system. Don't use it if you don't.

> **No path sandboxing.** The agent can read, write, and delete from any accessible path. There are no guardrails beyond the deletion confirmation check.
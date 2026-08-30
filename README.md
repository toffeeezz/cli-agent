# CLI Agent (DEVELOPMENT)

An interactive terminal agent/companion wrapper built with Python and `rich` for a school project and my personal use.

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
- **Graphical Window Interface** — A PyQt-based GUI. Apparently this is required for the project so here we are

## 💡 Experimental Ideas

- **Personality Development** — Simulate personality evolution through stored memories. This is the only feature in this category that might actually happen in the far future
- **Hyprland / Quickshell Integration** — Might implement this one if I don't get bored. Although highly unlikely.

---

## ⚠️ Limitations (MUST READ!!)

> **INTENDED FOR PERSONAL USE!!** This project is intended for people who know what they're doing. Don't use it if you lack the knowledge of the dangers of letting an AI agent run freely in your system.

> **NO PATH SANDBOXING!!** The agent does not have any clear sandboxing or safety guardrails so it may peek inside paths that shouldn't be allowed. The only protection is the deletion confirmation check, and that's not enough to call it safe.

> **SECRETS LEAKAGE!!** This agent reads files and sends their contents straight to the LLM — including any sensitive info like API keys, tokens, or passwords from `.env` files or config files. If you're running this, make damn sure you're not accidentally feeding secrets into a model prompt. **Never** let the agent read your `.env` unless you're okay with those values being transmitted externally.
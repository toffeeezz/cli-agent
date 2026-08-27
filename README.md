# CLI Agent (DEVELOPMENT)
An interactive terminal agent/companion wrapper built with Python and `rich` for a school project and my personal use.

---

## Implemented Features
* **Terminal History & Tab Completion**: Full support for arrow-key command history and Tab-based auto-suggestions for all internal commands
* **Command Tools**: Built-in internal commands to allow at-runtime modifications of environment variables, model and service switching, etc.
* **Multi-line Mode**: Allows for parsing long paragraphs or deep blocks of code seamlessly
* **Agentic AI**: Allow for the LLM model to behave like a standard agent
* **Tools Plugins**: Allow for the agent to call tools on-demand. Current tools include:
  - **File Tools**: `read_file`, `write_file`, `list_dir` — read, create, and explore files and directories
  - **Git Tools**: `git_status`, `git_add`, `git_commit` — check repo status, stage files, and commit changes

## Upcoming Features & Short-Term Goals
* **Skills Plugins**: Allow for the agent to utilize skills on-demand
* **Persona**: Allow for the agent to role-play a persona which is modifiable at-runtime
* **Memory Recall**: Allow for the agent to recall contextually relevant memories
* **Guard Rails**: Require the agent to request a confirmation from the user when doing tasks like deleting data, etc.
* **Long Term Memory Storage**: Allow for the agent to store memories that are scored by importance and significance
* **Graphical Window Interface**: A GUI window made from PyQt. Apparently this is required for our project so here we are

## Experimental Ideas & Future Pipeline
* **Personality Development**: Allow for the agent to simulate the evolution of a personality using the stored memories. The only feature in this category that might have a better chance of being implemented in the far-future
* **Integration for Hyprland/Quickshell setup**: Might implement this one if I don't get bored. Although highly-unlikely

---

## Limitations (MUST READ!!)
* **INTENDED FOR PERSONAL USE!!**: This project is intended for personal use only and for people who know what they are doing. It shouldn't be used by anyone who lacks the knowledge of the dangers of letting an AI agent run freely in your system
* **NO PATH SANDBOXING!!**: The agent does not have any clear sandboxing or safety guardrails so it may peek inside paths that shouldn't be allowed
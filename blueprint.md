# MODULES

## Command Line Interface (CLI)
* **Job:** Acts as the **user interaction layer**. It captures user commands or text input, kicks off the agent session, and formats the agent's internal reasoning and text output into clean, real-time terminal displays.

## Agent Core
* **Job:** Acts as the **central state machine and orchestrator**. It controls the main execution loop, determines the next operational step based on the model's choices, and passes data between memory, tools, and the LLM.

### Prompt Engine
* **Job:** Acts as the **context assembler**. It dynamically compiles system instructions, active session history, external data inserts, and valid tool definitions into a single structured prompt payload for the language model.

### LLM Client
* **Job:** Acts as the **foundation model gateway**. It handles external API connectivity, enforces strict JSON or schema outputs from the model, and safely manages API errors, rate limits, and token counters.

## Tool Registry
* **Job:** Acts as the **capabilities catalog**. It acts as an organized directory that stores functional code blocks (APIs, file utilities, database connectors) along with their structured metadata schemas so the agent knows what actions it can take.

### Skill Loader
* **Job:** Acts as the **plugin installer**. It dynamically scans external directories, resolves library dependencies, and mounts new programmatic skills or toolkits into the tool registry at startup or runtime.

## Memory
* **Job:** Acts as the **context preservation layer**. It maintains the immediate chat sequence (short-term episodic memory) and queries vector databases to retrieve relevant historical interactions or knowledge documents (long-term semantic memory).

### Persona Swaps

## Logger
* **Job:** Acts as the **system auditor**. It intercepts raw outputs, errors, and JSON execution payloads across all modules, formatting them into structured, timestamped logs for performance auditing and tracing.

## Development/Debugging Tools
* **Job:** Acts as the **developer sandbox**. It provides local environments to mock LLM responses, isolate prompt templates for quick iteration, and replay historical execution states to diagnose logic bugs.

"""SaktiAI — the AI Brain of SaktiLinux AI.

An operating-system brain, not a chatbot. Modular, offline-first,
Clean-Architecture engine that routes natural language through memory,
context, planning, commands, actions, voice, and local LLMs.

Submodules
----------
core        orchestrator, types, intent routing
memory      persistent user memory store
context     live system context sensing
planner     task -> step decomposition
command     natural language -> system commands
actions     understand -> plan -> validate -> execute -> verify -> report
voice        wake word + voice pipeline
llm         local LLM (Ollama) loading/unloading
providers   provider (local/cloud) switching
plugins     plugin SDK + registry
dev         developer core: project detection + real run/install/build
"""

__version__ = "0.7.0"
__all__ = ["core", "memory", "context", "planner", "command",
           "actions", "voice", "llm", "providers", "plugins", "dev",
           "tools", "automation"]
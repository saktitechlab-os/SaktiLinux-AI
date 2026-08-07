# SaktiAI — AI Brain

SaktiAI turns natural language into verifiable system actions. It is the
"brain" of SaktiLinux AI: offline-first, privacy-first, and modular.

## Pipeline

```
text → IntentClassifier → ContextEngine → TaskPlanner
     → CommandTranslator → ActionPipeline → MemoryStore → ExecutionReport
```

`SaktiBrain.process(text)` runs the whole pipeline and returns an
`ExecutionReport`. All stages are injectable (constructor injection), so
the CLI, the desktop sidebar, the voice engine, and tests can wire any
combination — including stubs.

## Modules

| Module | Responsibility |
| --- | --- |
| `ai/core` | `SaktiBrain` orchestrator, `IntentClassifier`, domain types |
| `ai/context` | `ContextEngine` — live OS / CPU / RAM / app / project / internet |
| `ai/planner` | `TaskPlanner` — intent → ordered, verifiable steps |
| `ai/command` | `CommandTranslator` — steps → shell commands (strict allow-list) |
| `ai/actions` | `CommandRunner` + `ActionPipeline` — execute, verify, dry-run |
| `ai/memory` | `MemoryStore` (JSON, XDG) + `MemoryBus` (events) |
| `ai/voice` | `WakeWord` ("Hey Sakti") + `VoiceEngine` (STT/TTS) |
| `ai/llm` | `LLMClient` (OpenAI-compatible) + `LLMRegistry` |
| `ai/providers` | `ProviderManager`, `Provider` ABC, `OllamaProvider` |
| `ai/plugins` | `SaktiPlugin` ABC + `PluginLoader` |

## Usage

```bash
# CLI (repo)
python3 -m ai.cli chat "install docker" --dry-run
python3 -m ai.cli status
python3 -m ai.cli memory list
python3 -m ai.cli providers list
python3 -m ai.cli plugins list
python3 -m ai.cli wake "hey sakti run a scan"

# or via script
scripts/sakti-ai chat "create a react portfolio" --dry-run
```

## Python API

```python
from ai.core import SaktiBrain
from ai.context import ContextEngine
from ai.planner import TaskPlanner

brain = SaktiBrain(context_engine=ContextEngine(), planner=TaskPlanner())
report = brain.process("install docker", dry_run=True)
print(report.message)          # "Completed N step(s)..."
print(report.intent.kind)      # IntentKind.INSTALL
print(report.to_dict())        # JSON-serializable full report
```

## Security Model

- `CommandTranslator` runs in **strict mode** by default: commands whose
  head is not on the platform allow-list are refused (returned empty) and
  never executed.
- `ActionPipeline` supports **dry-run** (plan but don't touch the system).
- Execution is fail-fast by default; `continue_on_error=True` is opt-in.
- Destructive/system-level actions are planned but require explicit user
  confirmation before real execution (Phase 3b wiring).

## Tests

```bash
python3 -m unittest discover -s ai/tests/unit -v        # 80+ unit tests
python3 -m unittest discover -s ai/tests/integration -v # end-to-end, dry-run
```

All tests are hermetic: memory/plugins/providers use temp dirs, and no
real commands are executed (dry-run or stub runners).

## Extending

- **New intent**: add a pattern in `ai/core/intent.py`, a rule in
  `ai/planner/planner.py` (`PLANNER_RULES`), then tests.
- **New provider**: subclass `Provider` in `ai/providers/` and register in
  `BUILTIN_PROVIDERS`.
- **New plugin**: drop a module with `class Plugin(SaktiPlugin)` into
  `~/.local/share/sakti/plugins/`; it is auto-loaded by `PluginLoader`.

## Roadmap (Phase 3b)

- Assistant service (systemd, D-Bus/gRPC) exposing the brain to the shell.
- Super+Space in-shell wiring (AI sidebar → brain).
- LLM-ranked intent candidates when a local provider is available.
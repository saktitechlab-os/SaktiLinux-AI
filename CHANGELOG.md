# Changelog

All notable changes to SaktiLinux AI are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Phase 3 — SaktiAI Brain execution & CLI fixes

#### Added

- **`scripts/sakti-ai` is now a Python entry point** — `python scripts/sakti-ai
  chat "hello"` (and `./scripts/sakti-ai`, `sakti`) all work. Previously it was
  a bash script, so `python scripts/sakti-ai` failed with a SyntaxError.
- **`python -m ai.core`** module entry point (`ai/core/__main__.py`).
- **Debug logs** on every pipeline stage: request, intent, context, plan
  steps, translated commands, per-step results, and final message.
- **Ollama detection** — `chat`/`status`/`providers` report when Ollama is
  registered but not running, with `ollama serve` guidance.
- **Conversational fallback for chat intents** (`general`) — answered directly
  instead of "verification failed".
- **Error surfacing** — brain pipeline never fails silently; exceptions are
  caught and printed with a traceback; unknown memory namespaces show a clear
  error and exit 1.
- **CLI smoke tests** (`ai/tests/integration/test_cli.py`) execute the real
  entrypoints: `chat "hello"`, `chat "install docker"`, `status`,
  `memory list`, `memory list projects`, `python -m ai.cli`, `python -m ai.core`.
- **Real-world validation suite** (`ai/tests/integration/test_real_execution.py`):
  - Real subprocess execution (stdout capture, exit codes, pipeline verify)
  - Failure scenarios: missing executables, non-zero exits, timeouts,
    empty commands, fail-fast
  - Unsafe-command blocking with a sentinel-file proof that destructive
    commands never execute

#### Fixed

- **Command allow-list bypass (security):** the strict-mode translator only
  checked the first token, so payloads like `echo 'rm -rf /' | bash` or
  `echo x; rm -rf /` smuggled past it. The allow-list now rejects any
  command containing `|`, `&&`, `||`, `;`, backticks, `$(`, or newlines.

## [v0.3.0-ai-brain] - 2026-08-07

Tagged release of Phase 3. See [release notes](docs/release-notes/v0.3.0-ai-brain.md).

## [0.3.0] - 2026-08-07

### Phase 3 — SaktiAI Brain

#### Added

- **SaktiAI orchestrator** (`ai/`):
  - `ai/core/brain.py` — `SaktiBrain` pipeline; DI-driven, testable stages.
  - `ai/core/intent.py` — rule-based intent classifier (10 intents).
  - `ai/core/types.py` — domain types (Intent, Plan, Step, ContextSnapshot,
    ActionResult, ExecutionReport).
- **Planning** (`ai/planner/`) — `TaskPlanner` per-intent strategies.
- **Command layer** (`ai/command/`) — `CommandTranslator` with strict-mode
  allow-list + template substitution.
- **Actions** (`ai/actions/`) — `CommandRunner` (timeout, dry-run) and
  `ActionPipeline` (fail-fast / continue, verification).
- **Memory** (`ai/memory/`) — JSON-backed `MemoryStore` (history, commands,
  projects, preferences, pinned, workspaces) + `MemoryBus` events.
- **Context** (`ai/context/`) — `ContextEngine` live sensing (OS, CPU/RAM,
  active app, git project, internet probe).
- **Voice** (`ai/voice/`) — `WakeWord` ("Hey Sakti") + `VoiceEngine`.
- **LLM** (`ai/llm/`) — `LLMClient` (OpenAI-compatible, stdlib-only) +
  `LLMRegistry`.
- **Providers** (`ai/providers/`) — `ProviderManager`, `Provider` ABC,
  `OllamaProvider`.
- **Plugins** (`ai/plugins/`) — `SaktiPlugin` ABC + `PluginLoader`.
- **CLI** — `scripts/sakti-ai` + `python -m ai.cli`
  (`chat`, `status`, `memory`, `providers`, `plugins`, `wake`).
- **Tests** — 88 tests under `ai/tests/unit` + `ai/tests/integration`.
- **Docs** — `docs/release-notes/v0.3.0-ai-brain.md`; `ai/README.md`;
  ROADMAP Phase 3 status.

## [v0.2.0-desktop] - 2026-08-07

Tagged release of Phase 2. See [release notes](docs/release-notes/v0.2.0-desktop.md).

## [0.2.0] - 2026-08-06

### Phase 2 — Desktop Experience

#### Added

- **Work Mode Manager** (`desktop/mode_engine.py` + `sakti-modes` CLI):
  - Dynamic mode switching: `default` / `developer` / `designer` / `cyber`
  - Applies accent color, wallpaper, dock apps, and shortcuts per mode
  - Installed apps are never removed — only UI surfaces change
  - Idempotent; Plasma-safe reloads
- **Mode definitions** (`desktop/modes/*.json`) with schema validation
- **Sakti plasmoids** (Plasma 6, Qt6 QML):
  - `org.kde.plasma.sakti.ai` — AI sidebar
  - `org.kde.plasma.sakti.spotlight` — Raycast-style launcher (Super+Space)
  - `org.kde.plasma.sakti.controlcenter` — glass control center
  - `org.kde.plasma.sakti.notifications` — notification center
  - `org.kde.plasma.sakti.workspaces` — dynamic workspace switcher
  - `org.kde.plasma.sakti.clock` — glass clock widget
- **Theme pipeline** (`themes/generate.py`):
  - KDE color schemes `Sakti-{cyan,indigo,orchid}.colors` from brand tokens
  - Plasma theme + splash scaffolding
- **Login screen** — `themes/sddm/sakti-login` (glass QML SDDM theme)
- **Wallpapers** — per-mode themed SVG wallpapers
- **Icon system** — Font Awesome style SVG icons + `SaktiIcons` theme
  (`scripts/install-icons.sh`)
- **Fonts** — Inter / JetBrains Mono / Geist install (`scripts/install-fonts.sh`)
- **Installers**:
  - `scripts/install-desktop.sh` (system-wide, idempotent)
  - `scripts/apply-user-shell.sh` (per-user config)
- **Tests** — `tests/unit/test_desktop.py` (modes, schemes, plasmoids, wallpapers)
- **Docs** — `docs/architecture/desktop.md`; architecture overview updated

## [0.1.0] - 2026-08-06

### Phase 1 — Architecture, Folder Structure, Branding, Base System

#### Added

- Full top-level project structure for all 15 roadmap phases
- Brand identity:
  - `branding/logo.svg` — lotus-core AI mark
  - `branding/colors.json` — canonical design tokens (palette, glass, type)
  - `branding/brand-guide.md` — brand story, usage, typography
- Architecture documentation:
  - `docs/architecture/overview.md` — system architecture & layer map
  - `docs/architecture/ai-brain.md` — SaktiAI design
  - `docs/architecture/runtime.md` — Universal Runtime design
  - `docs/architecture/security.md` — security model
  - `docs/guides/development.md` — development environment guide
  - `docs/guides/contribution.md` — contribution guidelines
- Base system:
  - `scripts/bootstrap-base.sh` — base-system bootstrap (VM / target)
  - `scripts/build-iso.sh` — ISO build pipeline (Phase 15)
  - `scripts/common/lib.sh` — shared shell library
  - `packages/lists/base.txt` — base package manifest
  - `packages/lists/dev.txt` — developer mode packages
  - `packages/lists/designer.txt` — designer mode packages
  - `packages/lists/cyber.txt` — cyber mode packages
- Repository governance:
  - `README.md`
  - `ROADMAP.md`
  - `CHANGELOG.md`
  - `LICENSE` (GPL-3.0)
  - `.gitignore`
- Tests:
  - `tests/run-tests.sh` — test runner
  - `tests/unit/test_structure.py` — structure validation
  - `tests/unit/test_packages.py` — package manifest validation
  - `.github/workflows/ci.yml` — CI pipeline

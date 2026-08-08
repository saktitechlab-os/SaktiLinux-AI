# Changelog

All notable changes to SaktiLinux AI are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.5.0] — 2026-08-07

### Phase 4A — Developer Core

#### Added

- **History system completion** — full unit + integration test coverage for
  the persistent dev command history:
  - Store: default cap of **50** verified (`list` keeps newest 50,
    `list(limit=)` slicing), monotonic ids continue across reloads, `get`
    returns unknown ids as `None` and returns copies, persistence across
    reloads.
  - Engine: `history_list()` returns recorded entries and honors `limit`,
    returns `[]` without a store; `replay()` re-runs stored commands,
    missing-id fails with exit -5, dry-run replays never execute.
  - CLI integration: `dev history` listing, empty state, `dev replay`
    end-to-end, **failure replay** reproduces a failing command and records
    the replay as `FAIL`, dry-run replay leaves no side-effect, failed
    installs are recorded as `fail`.
- **Tests** — 11 new (7 unit: cap-50 default, list slicing, get-unknown/
  copy-safety, id monotonicity + continuation across reload, engine
  history_list with/without store; 4 integration: failing replay, failed
  install recorded). Full suite now **226 AI tests + 14 Phase 1-2 tests**.
- Version bumped to **0.5.0**.

## [Unreleased]

### Phase 4A — Developer Core

#### Added

- **History filtering, search, export, clear** (extends the command
  history):
  - `sakti-ai dev history --status success|fail|dry-run` and
    `--action run|install|build|replay` filter the listing.
  - `sakti-ai dev history search <text>` — case-insensitive substring
    search over command/cwd/action/status/timestamp (exit 1 when no match).
  - `sakti-ai dev history export [--format json|csv|md] [--output FILE]
    [--status S] [--action A]` — serialize to stdout or a file.
  - `sakti-ai dev history clear [--yes]` — confirm-and-erase the log
    (ids stay monotonic, so replay ids remain stable).
  - Store (`DevHistory`) gained `list(status=, action=)`, `search()`, and
    `format_export()` helpers.
- **Tests** — 22 new (12 unit: filter/limit/search/export roundtrips; 10
  integration: CLI filter/export/clear/search incl. stdin-abort). Full
  suite now **215 AI tests + 14 Phase 1-2**.

### Phase 4A — Developer Core

#### Added

- **Command history + replay** (`ai/dev/history.py`):
  - `DevHistory` — persistent JSON store of the last 50 dev commands
    (default at `~/.local/share/sakti/dev_history.json`, atomic writes,
    monotonic ids safe to replay after trimming).
  - Each entry records the **timestamp**, **success/failure status**
    (`success` / `fail` / `dry-run`), exit code, action (run/install/
    build/replay), cwd, and the full command line.
  - Every engine execution is recorded automatically; replays are
    recorded as their own entries.
  - CLI: `sakti-ai dev history [--limit N]` lists newest-first with
    status and timestamps; `sakti-ai dev replay <id> [--dry]` re-runs a
    stored command in its original directory (dry-replay never executes,
    unknown ids fail with exit -5).
- **Tests** — 18 new tests (13 unit: store add/cap/persistence/clear/
  statuses, engine recording + replay incl. dry and unknown-id; 5
  integration: CLI history listing, empty-state, replay end-to-end,
  unknown-id failure, dry-replay no-side-effect). Full suite now
  **195 AI tests + 14 Phase 1-2 tests**.

### Phase 4A — Developer Core

#### Added

- **Live output streaming** (`ai/actions/runner.py` `run_live`) — dev
  commands stream stdout/stderr line-by-line as they are produced (with an
  optional `on_line` callback), instead of only showing the final output.
  Dev CLI runs live by default; `--no-live` opts back into buffering.
- **Dry-run mode** for dev commands — `sakti-ai dev run|build [--dry]`,
  `sakti-ai dev install <dep> --dry` print the exact command that *would*
  run (`[dry-run] ...`) and never execute it (verified with a sentinel-file
  test). Dry-run also skips the install confirmation prompt.
- **Install confirmation** — `sakti-ai dev install <dep>` now asks
  `Install <dep>? [y/N]` before modifying the environment; `--yes`/`-y`
  skips the prompt, answering no aborts with exit code -4 without running
  anything.
- **Human-readable error hints** (`ai/dev/errors.py`) — when npm/pip/
  composer fails, `diagnose()` maps common failures (E404, EACCES,
  ERESOLVE, "No matching distribution", PEP 668 externally-managed, SSL/
  network, command-not-found, disk full, timeouts) onto an actionable
  `[fix] ...` line appended to stderr.
- **Tests** — 19 new tests (12 unit: confirmation accept/decline, dry-run
  plumbing, live dispatch, `diagnose` hints; 7 integration: real
  line-by-line streaming incl. incremental ordering + stderr + timeout,
  dry-run filesystem sentinel, failed-install hint, CLI `--dry --yes`).
  Full suite now **177 AI tests + 14 Phase 1-2 tests**.

### Phase 4A — Developer Core

#### Added

- **`ai/dev/` Developer Core** — real developer workflows, no placeholders:
  - `DevContextDetector` (`ai/dev/detector.py`) — filesystem project sniffing
    for Node.js, Python, and PHP: project type, language (javascript /
    python / php), framework (react, next, vite, vue, express, django,
    fastapi, flask, laravel, symfony, ...), and package manager (npm, yarn,
    pnpm, bun, pip, poetry, uv, composer) from manifests and lockfiles.
  - `DevCommandEngine` (`ai/dev/engine.py`) — real execution of the three
    required developer commands:
    - `run_project` — dev-server/npm script, python entry (main/manage/app),
      php built-in server; runs from the detected project root.
    - `install_dependency` — right installer per ecosystem (`npm install`,
      `yarn add`, `pip install` via the running interpreter, `composer
      require`, ...) with validated command construction.
    - `build_project` — npm build script, `python -m compileall`, composer
      install.
  - `CommandRunner` gained per-call `cwd` support so commands run inside the
    project (not the host process directory).
- **CLI** — `sakti-ai dev status|run|install|build`:
  - `sakti-ai dev status [--path DIR]` — prints detected type / language /
    framework / package manager / name / root.
  - `sakti-ai dev run [--path DIR] [--script NAME] [--arguments ...]`
  - `sakti-ai dev install <dependency> [--path DIR] [--manager M]`
  - `sakti-ai dev build [--path DIR]`
- **Tests** — 34 new tests (23 unit `ai/tests/unit/test_dev.py` + 11
  integration `ai/tests/integration/test_dev_execution.py`) covering
  detection across all three ecosystems and lockfiles, command
  construction, unsupported-project failures, and **real** execution
  (node/npm guarded by availability; real pip install of `six`; compileall;
  CLI end-to-end).
- **Intent classifier hardened** (from the Phase-3→4 review): fixed the
  package-manager capture group (`_extract_dep`), the `dev server` run
  pattern (braces were interpolated away by an f-string), and re-anchored
  generic `install`/`build` targets.
- Version bumped to **0.4.0**.

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

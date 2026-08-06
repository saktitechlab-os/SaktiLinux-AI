# Changelog

All notable changes to SaktiLinux AI are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

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

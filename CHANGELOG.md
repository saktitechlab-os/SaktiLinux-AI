# Changelog

All notable changes to SaktiLinux AI are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

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

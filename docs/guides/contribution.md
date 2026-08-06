# Contribution Guide

## Code of Conduct

Be respectful, constructive, and focused. AI-native systems demand rigor.

## How to Contribute

1. **Pick a phase** — see `ROADMAP.md`. Do not start ahead of the active phase
   unless explicitly approved.
2. **Read first** — understand `docs/architecture/overview.md` and the target
   subsystem doc before touching code.
3. **Follow Clean Architecture & SOLID** — modules are decoupled; reuse existing
   modules; never duplicate logic.
4. **No placeholders** — never commit pseudo-code or TODO stubs; if a feature
   is not ready, it belongs in the roadmap, not the codebase.
5. **Tests** — every change ships with passing tests. Run the suite
   (`bash tests/run-tests.sh`) before pushing.
6. **Commit style** — conventional commits:
   `feat:`, `fix:`, `docs:`, `test:`, `chore:`, `refactor:`.
7. **Changelog** — update `CHANGELOG.md` for user-visible changes.

## Security

- Report vulnerabilities privately: open a confidential issue or contact
  maintainers directly. Do not open public PoCs.
- Never commit secrets, credentials, disk images, or VM artifacts —
  they are `.gitignore`d for exactly this reason.
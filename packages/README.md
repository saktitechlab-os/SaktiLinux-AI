# Packages

Arch package manifests power every install path: base system, work modes,
and (later) the AI Store.

## Manifests

| File | Purpose | Used by |
| --- | --- | --- |
| `lists/base.txt` | Core OS packages | `bootstrap-base.sh`, ISO |
| `lists/dev.txt` | Developer Mode | Bootstrap `--with-dev`, Phase 4 |
| `lists/designer.txt` | Designer Mode | Phase 5 |
| `lists/cyber.txt` | Cyber Mode | Phase 6 |

Format: one Arch package per line; `#` comments allowed; no duplicates.

Validated by `tests/unit/test_packages.py` in CI.
# Security Architecture

## 1. Trust Model

- **Base system** signed by project keys.
- **Apps** run through scoped sandboxes; AI actions pass an allowlist policy.
- **AI malware detection** (`security/`) inspects new binaries, manifests, and
  runtime behavior, learning local heuristics offline.

## 2. Layers

| Layer | Mechanism |
| --- | --- |
| Firewall | nftables (zero-default-deny for services) |
| Sandbox | bubblewrap / firejail app profiles |
| Permissions | **Permission Manager** — app permission grants per capability |
| Malware | AI malware detection service |
| Upgrades | Signed OTA, atomic, rollback-safe (Phase 11) |
| Kernel | `kernel/` hardening params (Phase 1 base placeholder) |
| Build | Reproducible manifests; CI validates structure & manifests |

## 3. Current Phase-1 Assets

- `security/` design docs and package lists.
- Firewall / sandbox / permission manager implemented in Phase 13.
- `tests/unit/test_packages.py` validates that security-related manifests stay
  structurally valid as packages evolve.

## 4. Secure Development

- No secrets committed; `.gitignore` excludes VM/disk/credentials artifacts.
- CI runs tests & structure validation on every push/PR.
- See `docs/guides/contribution.md` for reporting process.
# SaktiLinux AI — Fonts

The desktop uses three families:

| Font | Role | Source |
| --- | --- | --- |
| **Inter** | UI, body, labels | Arch repo `inter-font` (or `ttf-inter` in AUR) |
| **JetBrains Mono** | Code, terminal, data | Arch repo `ttf-jetbrains-mono` |
| **Geist** | Display, headlines, big numbers | Vercel Geist — download & install locally |

## Install

```bash
sudo pacman -S --needed inter-font ttf-jetbrains-mono
./scripts/install-fonts.sh
```

## Geist license

Geist is open source under the SIL Open Font License (OFL-1.1).
Official release: https://github.com/vercel/geist-font

## Why offline-first

Fonts are shipped inside the SaktiLinux ISO (Phase 15) so the OS never
needs network access to look premium.

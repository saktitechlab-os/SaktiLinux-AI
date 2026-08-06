# SaktiLinux AI

**The AI Native Linux Distribution.**

SaktiLinux AI is a production-grade, AI-first Linux operating system built on
Arch Linux, Wayland, and KDE Plasma. Instead of searching through menus, you
talk to **SaktiAI** — the always-running assistant (Super + Space, or "Hey Sakti").

## Mission

Build the world's most intelligent Linux operating system — AI first, open
source, offline-first, privacy-first, and beautiful.

## Project Status — Phase 2 (In Progress)

Phase 1: Architecture, Folder Structure, Branding, Base System ✅
Phase 2: Desktop Experience, Dynamic Workspace Modes ✅
See [ROADMAP.md](ROADMAP.md) and [CHANGELOG.md](CHANGELOG.md).

## Desktop Highlights (Phase 2)

- **Dynamic Workspace Modes** — `sakti-modes switch developer|designer|cyber`
  re-shapes the dock, launcher, widgets, shortcuts, accent color, and
  wallpaper. Installed apps are never removed — only UI changes.
- **Floating glass shell** — dock, taskbar, control center, notification
  center, spotlight search, AI sidebar.
- **Theme pipeline** — `branding/colors.json` → KDE color schemes per accent.
- **Font Awesome style SVG icons**, Inter / JetBrains Mono / Geist fonts.
- **Glass SDDM login screen** and per-mode wallpapers.

## Top-Level Structure

```
docs/          Architecture, guides, security docs
branding/      Logo, colors, brand guide
desktop/       Mode engine, mode defs, plasmoids, shell components
ai/            SaktiAI brain, memory, search, automation
kernel/        Kernel configuration and tuning
installer/     Beautiful ISO installer
sdk/           Plugin SDK for third-party modules
packages/      Package lists per work mode & runtime catalogs
runtime/       Universal Runtime (Flatpak, Snap, AppImage, Wine, Waydroid)
settings/      Modern settings app (AI-explainable)
store/         AI Store — one-click installs
terminal/      AI Terminal
voice/         Voice assistant — wake word, STT, TTS
security/      Firewall, sandbox, permissions, AI malware detection
plugins/       Bundled plugins
scripts/       Build, install & automation scripts
themes/        Theme generator, color schemes, SDDM login theme
tests/         Test suites
assets/        Icons (FA style), wallpapers, fonts
.github/       CI/CD
```

## Core Principles

AI First · Open Source · Modern UI · Beautiful UX · Fast · Secure ·
Offline First · Privacy First · Modular · Scalable · Maintainable

## Tech Stack

Arch Linux · Wayland · KDE Plasma · Rust · C++ · Python · TypeScript ·
Ollama · llama.cpp · Open WebUI

## Work Modes

- **Developer Mode** — VS Code, Cursor, OpenCode, Docker, Git, Databases, Terminal
- **Designer Mode** — Blender, Penpot, Krita, Inkscape, Assets, Gallery
- **Cyber Mode** — Burp Suite, Wireshark, Nmap, Metasploit, Terminal, Browser

## Quick Start (Development)

Development currently targets an Arch Linux virtual machine
(`SaktiOS dev`, VirtualBox, host SSH on port 3022).

1. Start the VM.
2. `ssh -p 3022 saktios@127.0.0.1`
3. `git clone` this repository, then run `scripts/bootstrap-base.sh`.
4. For the desktop shell: `sudo bash scripts/install-desktop.sh` and
   reboot (or restart SDDM). Switch workspaces with `sakti-modes switch <mode>`.

See [docs/guides/development.md](docs/guides/development.md).

## License

GPL-3.0 — see [LICENSE](LICENSE).

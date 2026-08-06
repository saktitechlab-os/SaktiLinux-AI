# SaktiLinux AI — Roadmap

## Phase 1 — Architecture, Folder Structure, Branding, Base System ✅

- [x] Project structure
- [x] Brand identity (logo, colors, brand guide)
- [x] Architecture documentation
- [x] Base system bootstrap scripts
- [x] Package manifests
- [x] Tests & CI
- [x] README / CHANGELOG / ROADMAP / LICENSE

## Phase 2 — Desktop ✅

- [x] Dynamic Workspace Mode system (default / developer / designer / cyber)
- [x] Global theme generation (Inter, JetBrains Mono, Geist fonts)
- [x] Floating Dock (mode-driven)
- [x] Floating Taskbar
- [x] Control Center (glass applet)
- [x] Notification Center (smart grouping)
- [x] Spotlight Search (Super+Space)
- [x] AI Sidebar applet
- [x] Login screen (SDDM glass theme)
- [x] Lock screen (SDDM-based)
- [x] Modern Widgets (clock, workspaces)
- [x] Workspace switcher (mode-aware)
- [x] Rounded windows + blur/acrylic (KWin compositing + theme)
- [x] Smooth animations
- [x] Dynamic wallpapers (per mode)
- [x] Dynamic accent colors (cyan / indigo / orchid)
- [x] Font Awesome SVG icon system (SaktiIcons)
- [ ] Boot animation refinement (with splash in Phase 15 ISO)

## Phase 3 — AI Brain

- [ ] SaktiAI assistant service (Ollama / llama.cpp)
- [ ] AI Memory (projects, style, favorites, workspaces, commands)
- [ ] Voice assistant ("Hey Sakti")
- [ ] Super + Space shortcut
- [ ] Natural language → action engine
- [ ] AI context awareness

## Phase 4 — Developer Mode

- [ ] Mode detection & context switching
- [ ] VS Code / Cursor / OpenCode integration
- [ ] Docker, Git, Databases, Terminal tooling
- [ ] Hide unrelated apps

## Phase 5 — Designer Mode

- [ ] Blender, Penpot, Krita, Inkscape integration
- [ ] Assets & Gallery management
- [ ] Hide unrelated apps

## Phase 6 — Cyber Mode

- [ ] Burp Suite, Wireshark, Nmap, Metasploit integration
- [ ] Dedicated hardened terminal & browser profiles
- [ ] Hide unrelated apps

## Phase 7 — Universal Runtime

- [ ] Runtime detection & selection engine
- [ ] Flatpak / Snap / AppImage support
- [ ] Wine / Proton for Windows EXE & MSI
- [ ] Waydroid for Android APK
- [ ] Automatic best-runtime selection (zero user questions)

## Phase 8 — Store

- [ ] Beautiful store UI
- [ ] One-click install
- [ ] Developer / Designer / Cyber / AI app categories

## Phase 9 — Settings

- [ ] Modern, searchable settings app
- [ ] AI Explain button on every setting

## Phase 10 — Installer

- [ ] Beautiful graphical installer
- [ ] Automated partitioning
- [ ] OTA update readiness

## Phase 11 — Updater

- [ ] OTA update service
- [ ] Atomic / rollback-safe updates

## Phase 12 — Plugin SDK

- [ ] Public plugin SDK
- [ ] Plugin manifest & registry
- [ ] Sandboxed plugin execution

## Phase 13 — Security

- [ ] Firewall (nftables)
- [ ] Sandbox (bubblewrap / firejail)
- [ ] Permission manager
- [ ] AI malware detection

## Phase 14 — Testing

- [ ] Unit, integration, and E2E suites
- [ ] Performance & stability gate
- [ ] Security audit

## Phase 15 — ISO Builder & Public Release

- [ ] `scripts/build-iso.sh` production pipeline
- [ ] Release signing
- [ ] Public release

---

## Working Method

Every phase is delivered end-to-end (code + docs + tests + changelog + commit),
then we **stop** and wait for explicit confirmation before the next phase.

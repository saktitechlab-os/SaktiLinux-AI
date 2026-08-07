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

## Phase 3 — AI Brain ✅

- [x] SaktiAI brain orchestration (`ai/core`, `SaktiBrain`, report pipeline)
- [x] Natural language → action engine (intent classifier, planner, command
      translator, action pipeline with allow-listed execution)
- [x] AI Memory (projects, style, favorites, workspaces, commands)
- [x] AI context awareness (live system + project + internet context)
- [x] Voice baseline ("Hey Sakti" wake word + voice engine)
- [x] Local LLM layer (Ollama/llama.cpp providers, OpenAI-compatible client)
- [x] Plugin SDK foundation (loader, manifest, sandbox marking)
- [x] `sakti` CLI + `scripts/sakti-ai` entry point — tagged `v0.3.0-ai-brain`
- [ ] Assistant service (systemd D-Bus/gRPC) — Phase 3b/GUI integration
- [ ] Super + Space in-shell integration (AI sidebar → brain)

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

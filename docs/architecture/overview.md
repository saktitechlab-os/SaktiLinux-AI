# SaktiLinux AI — Architecture Overview

## 1. Design Philosophy

SaktiLinux AI is **AI First**: the AI is the primary interface. Traditional
desktop discovery (menus, launchers, settings browsing) is replaced by an
always-running assistant, **SaktiAI**, that understands natural language and
converts it into actions.

Core principles: AI First · Open Source · Modern UI · Beautiful UX · Fast ·
Secure · Offline First · Privacy First · Modular · Scalable · Maintainable.

## 2. Technology Stack

| Layer | Technology |
| --- | --- |
| Base OS | Arch Linux (rolling, reproducible via manifests) |
| Display | Wayland |
| Desktop shell | KDE Plasma (initial) with custom floating shell components |
| Languages | Rust, C++, Python, TypeScript |
| AI inference | Ollama + llama.cpp (offline-first) |
| AI UI | Open WebUI (web surface for models) |
| Systemd | init, services, socket activation |
| Packaging | pacman + manifests under `packages/` |

## 3. System Layers

```
+---------------------------------------------------------------+
|  AI First UX                                                   |
|  SaktiAI · Voice · Spotlight · AI Terminal · AI File Manager   |
+---------------------------------------------------------------+
|  Desktop Shell (KDE Plasma + custom components)                |
|  Floating Dock · Taskbar · Control Center · Notification Ctr   |
+---------------------------------------------------------------+
|  AI Brain                                                      |
|  Assistant Service · Memory · Search · Automation · Context    |
+---------------------------------------------------------------+
|  Services & Runtime                                            |
|  Universal Runtime · Store · Settings · Updater · Plugins      |
+---------------------------------------------------------------+
|  Security                                                      |
|  Firewall · Sandbox · Permission Manager · AI Malware Detect   |
+---------------------------------------------------------------+
|  Base System (Arch Linux)                                      |
|  kernel/ · packages/ · systemd units · bootstrap scripts       |
+---------------------------------------------------------------+
```

## 4. Directory Map

| Directory | Responsibility | Owner |
| --- | --- | --- |
| `docs/` | Architecture & guides | All |
| `branding/` | Identity, tokens, logo | Design |
| `desktop/` | Shell components, panels, widgets | Desktop team |
| `ai/` | SaktiAI brain, memory, automation | AI team |
| `kernel/` | Kernel config, modules, tuning | Kernel team |
| `installer/` | Graphical installer | Platform team |
| `sdk/` | Plugin SDK | Platform team |
| `packages/` | Manifests, catalogs, work-mode lists | Platform team |
| `runtime/` | Universal Runtime engine | Runtime team |
| `settings/` | Settings app backend/frontend | Desktop team |
| `store/` | Store backend & UI | Platform team |
| `terminal/` | AI Terminal | AI team |
| `voice/` | STT/TTS, wake word | AI team |
| `security/` | Firewall, sandbox, perms, malware AI | Security team |
| `plugins/` | Bundled plugins | All |
| `scripts/` | Build, bootstrap, tooling | Platform team |
| `themes/` | Global themes | Design |
| `tests/` | Test suites | QA |
| `assets/` | Icons, wallpapers, fonts | Design |

## 5. Key Subsystem Designs

### 5.1 SaktiAI Brain (`ai/`)
- Always-running systemd service.
- Interface: Super + Space overlay, voice wake "Hey Sakti".
- Inference: Ollama with offline llama.cpp models; Open WebUI as web surface.
- Natural-language action engine converts requests into vetted system actions
  (e.g., "install Docker", "create React project", "scan network").
- See `docs/architecture/ai-brain.md`.

### 5.2 Universal Runtime (`runtime/`)
- Single launch abstraction: given any app artifact, choose best runtime.
- Linux (native) → Flatpak → Snap → AppImage → EXE/MSI (Wine/Proton) → APK (Waydroid).
- Decision engine is automatic — no technical questions asked of the user.
- See `docs/architecture/runtime.md`.

### 5.3 Work Modes
- Developer / Designer / Cyber modes.
- Context-aware shell: relevant apps promoted, unrelated apps hidden.
- Mode driven by AI context + explicit switch; per-user profile under
  `packages/lists/`.

### 5.4 Security Model
- nftables firewall, bubblewrap/firejail sandbox, permission manager.
- AI malware detection service (`security/`).
- See `docs/architecture/security.md`.

## 6. Update & Delivery Model

- OTA update service (Phase 11) with atomic, rollback-safe upgrades.
- ISO built by `scripts/build-iso.sh` (Phase 15) using manifests in
  `packages/` for reproducibility.

## 7. Workflow Rules

1. Work is delivered **phase by phase** (see `ROADMAP.md`).
2. Each phase: code + docs + tests + changelog + commit.
3. We stop and wait for confirmation before the next phase.
4. Never break existing functionality; reuse modules; follow SOLID + Clean Architecture.

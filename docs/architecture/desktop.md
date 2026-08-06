# Desktop Experience — Architecture (Phase 2)

## 1. Vision

SaktiLinux AI's desktop must feel premium and never "like Linux": glass
surfaces, floating chrome, smooth motion, and an AI-first assistant that is
always one keystroke away. Design language: macOS clarity, Windows 11
fluidity, Arc Browser aesthetics, Nothing OS minimalism, Raycast efficiency,
glassmorphism everywhere.

## 2. Composition

| Component | Type | Implementation |
| --- | --- | --- |
| Floating Dock | Plasma panel | `desktop/plasmoids/*` + mode-driven panel config |
| Floating Taskbar | Plasma panel | mode-driven applets |
| Spotlight Search | Overlay applet | `org.kde.plasma.sakti.spotlight` (Super+Space) |
| AI Sidebar | Panel applet | `org.kde.plasma.sakti.ai` |
| Notification Center | Applet | `org.kde.plasma.sakti.notifications` |
| Control Center | Applet | `org.kde.plasma.sakti.controlcenter` |
| Workspace Switcher | Applet | `org.kde.plasma.sakti.workspaces` |
| Clock / Widgets | Applets | `org.kde.plasma.sakti.clock` + KDE widgets |
| Login / Lock | SDDM theme | `themes/sddm/sakti-login` |
| Window chrome | KWin | Blur + rounded panels via theme + compositing |
| Icons | SVG theme | `assets/icons/` → `SaktiIcons` |
| Fonts | Inter / JetBrains Mono / Geist | `scripts/install-fonts.sh` |

## 3. Dynamic Workspace Modes

The **Dynamic Workspace Mode** system is the heart of Phase 2.

```
sakti-modes switch developer
        │
        ▼
┌─────────────────────────────┐
│ ModeEngine (mode_engine.py) │
│  • read desktop/modes/*.json│
│  • apply color scheme       │
│  • apply wallpaper          │
│  • rewrite dock applets     │
│  • bind shortcuts           │
│  • reload plasmashell       │
└─────────────────────────────┘
```

Modes: `default` · `developer` · `designer` · `cyber`.

What changes per mode:

- **Dock**: app set per mode
- **Launcher / Start Menu**: per-mode grids
- **Widgets**: per-mode widget sets
- **Shortcuts**: per-mode global bindings
- **Accent color**: cyan / indigo / orchid (via generated `.colors` schemes)
- **Wallpaper**: per-mode themed SVG

**Guarantee:** installed applications are NEVER removed. Modes only re-shape
UI surfaces. App packages remain untouched.

## 4. Theme Pipeline

`branding/colors.json` (single source of truth) →
`themes/generate.py` →
`themes/color-schemes/Sakti-{cyan,indigo,orchid}.colors` +
Plasma theme + splash.

This keeps every surface (KDE widgets, Qt apps, shell panels) consistent
with the brand palette.

## 5. Component Contracts

- Plasmoid IDs follow `org.kde.plasma.sakti.*`.
- Every plasmoid ships `metadata.json` + `contents/ui/main.qml`.
- Panel config is written by `mode_engine._apply_dock()`; it regenerates
  `~/.config/plasma-org.kde.plasma.desktop-appletsrc` safely.
- `sakti-modes` is the only user-facing CLI for switching.

## 6. Phasing

- Phase 2 ships: shell, modes, themes, icons, fonts, login screen, widgets.
- Phase 3 replaces hardcoded `aiService` wiring in the AI sidebar with the
  real SaktiAI backend.

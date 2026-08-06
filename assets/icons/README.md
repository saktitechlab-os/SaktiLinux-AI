# SaktiLinux AI — Font Awesome SVG icon system

The desktop ships a Font Awesome style icon system: filled, rounded, modern
SVG icons on a consistent 24x24 grid, used by the dock, taskbar, control
center, spotlight, and AI surfaces.

## Set layout

```
assets/icons/
  index.theme           KDE icon theme metadata
  apps/                 app icons (vscode, blender, wireshark, …)
  actions/              action icons (search, settings, power, …)
  places/               places icons (folder, home, downloads, …)
  status/               status icons (wifi, battery, alert, …)
```

## Install

```bash
./scripts/install-icons.sh
```

Installs the theme to `~/.local/share/icons/SaktiIcons` (per-user) so no
root is needed, then refreshes the icon cache.

## Theme fallback

`SaktiIcons` inherits `breeze` and `hicolor`, so any icon we don't ship
falls back gracefully — installed apps always keep a usable icon.

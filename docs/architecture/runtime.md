# Universal Runtime — Architecture

## 1. Goal

Launch any application artifact through a single, automatic runtime that picks
the best available execution environment. The user is **never** asked technical
questions like "which runtime?" — it just works.

## 2. Supported Artifacts

| Artifact | Runtime |
| --- | --- |
| Linux native (`ELF`, `.deb`, `.rpm`, source) | Host pacman / native |
| `.flatpak` / Flatpak remote apps | Flatpak |
| `.snap` | Snap |
| `.AppImage` | AppImage (via FUSE) |
| `.exe` / `.msi` (Windows) | Wine (Proton for gaming/D3D) |
| `.apk` (Android) | Waydroid |

## 3. Decision Engine

```
+-------------+   +----------------+   +----------------+
| App Request |-->| Detect Type    |-->| Runtime Select  |
+-------------+   +----------------+   +----------------+
                                            |
                                  +---------+---------+
                                  | Availability Check |
                                  +---------+---------+
                                            |
                                    +---------------+
                                    | Launch & Sandbox|
                                    +---------------+
```

The engine scans content-type, magic bytes, package metadata (MIME, section),
and installed runtimes to resolve to exactly one launch strategy.

## 4. Runtime Backends — Planned Modules

- `runtime/detect` — artifact detection
- `runtime/flatpak` — Flatpak backend
- `runtime/snap` — Snap backend
- `runtime/appimage` — AppImage backend
- `runtime/wine` — Wine/Proton backend
- `runtime/waydroid` — Android (APK) backend
- `runtime/resolver` — decision engine (Rust)

## 5. Storage Isolation

- App data per runtime (XDG base dirs).
- Sandbox policies applied where the backend supports it.
- A **Universal App Launcher** (`runtime/launcher`) wraps every backend so the
  desktop shell sees a uniform API.

## 6. Phase Assignment

Implemented in **Phase 7**. Design only here (Phase 1).
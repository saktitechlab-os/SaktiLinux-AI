# SaktiAI — The AI Brain

## 1. Purpose

SaktiAI is the always-running AI assistant of SaktiLinux AI. It is the primary
interface: users express intent in natural language and SaktiAI turns it into
actions — no menu hunting, no CLI memorization.

## 2. Interfaces

| Surface | Trigger |
| --- | --- |
| Assistant overlay | `Super + Space` |
| Voice | Wake word "Hey Sakti" |
| AI Terminal | natural-language commands inline |
| AI File Manager | contextual suggestions |
| Spotlight | AI-ranked search |

## 3. Components

- **Assistant Service** (`ai/assistant`) — long-running systemd service.
- **Ollama Runtime** — local model serving (offline-first).
- **llama.cpp** — lightweight inference fallback / edge models.
- **Open WebUI** — model management & chat surface.
- **Memory Store** (`ai/memory`) — persistent user memory.
- **Action Engine** (`ai/actions`) — maps natural language → system actions.

## 4. AI Memory

Persisted per-user, stored locally (privacy-first):

- Projects
- Coding style / preferences
- Frequently used apps
- Favorite IDE
- Pinned files & projects
- Workspaces
- Recent commands

## 5. Natural Language → Action Engine

Example intents and their action mappings:

| Intent | Action |
| --- | --- |
| "Create React project" | `npx create-react-app` in chosen dir |
| "Install Docker" | package install + service enable |
| "Build Android app" | scaffold + build pipeline |
| "Generate portfolio" | project generator |
| "Scan network" | nmap wrapper (cyber mode) |
| "Organize Downloads" | file-manager auto-organize |
| "Deploy website" | static or container deploy |

## 6. Security Guardrails

- All actions undergo an allow/deny policy check.
- Destructive actions require explicit user confirmation.
- Runs with least privilege; drop to per-task scoped elevation.

## 7. Interfaces

Defined later (Phase 3) as:
- `ai-brain` gRPC / D-Bus service
- typed `sakiai-sdk` client binding for Rust, Python, TypeScript
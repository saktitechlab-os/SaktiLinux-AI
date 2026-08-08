#!/usr/bin/env sh
# SaktiOS — fullscreen UI shell launcher (Phase 6).
#
# Started by the Hyprland/Openbox autostart config written via
# `sakti-ai ui install`. Responsible for:
#   1. starting the SaktiOS UI web server (sakti-ai ui serve)
#   2. opening the fullscreen window that shows it
#   3. keeping only the SaktiOS shell visible (no panels, no bars)
#
# Window strategy (lightest first):
#   - pywebview  -> native frameless fullscreen window (preferred)
#   - chromium   -> --app --kiosk (no browser chrome visible)
#   - firefox    -> --kiosk fallback
#   - xdg-open   -> last resort (WM may float it; ok on Hyprland)
set -e

UI_HOST="${SAKTI_UI_HOST:-127.0.0.1}"
UI_PORT="${SAKTI_UI_PORT:-8765}"
UI_URL="http://${UI_HOST}:${UI_PORT}"

ui_up() {
    # shellcheck disable=SC2086
    curl -sf -o /dev/null "${UI_URL}/api/status" 2>/dev/null
}

start_server() {
    if ! ui_up; then
        nohup sakti-ai ui serve --host "${UI_HOST}" --port "${UI_PORT}" \
            >/tmp/sakti-ui.log 2>&1 &
    fi
}

open_window() {
    if command -v python3 >/dev/null 2>&1 && \
       python3 -c "import pywebview" 2>/dev/null; then
        python3 - <<PY
import threading, time, webview, os
time.sleep(1)
webview.create_window("SaktiOS", "${UI_URL}",
                      fullscreen=True, frameless=True)
webview.start()
PY
    elif command -v chromium >/dev/null 2>&1; then
        chromium --app="${UI_URL}" --kiosk --noerrdialogs \
            --disable-session-crashed-bubble --disable-infobars &
    elif command -v chromium-browser >/dev/null 2>&1; then
        chromium-browser --kiosk "${UI_URL}" &
    elif command -v firefox >/dev/null 2>&1; then
        # first tab is the shell; kiosk hides the chrome
        firefox --kiosk "${UI_URL}" &
    else
        xdg-open "${UI_URL}" || echo "[sakti-ui] no window opener found"
    fi
}

start_server
open_window
echo "[sakti-ui] SaktiOS shell at ${UI_URL}"
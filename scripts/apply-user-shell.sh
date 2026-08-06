#!/usr/bin/env bash
# SaktiLinux AI — user-level shell configuration (dock, taskbar, fonts, icons)
# Runs as the target user (no root required). Idempotent.
#
# Usage: bash scripts/apply-user-shell.sh
#        (from install-desktop.sh via runuser, or directly)

set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common/lib.sh"

log_info "Applying Sakti user shell config"

# ----------------------------------------------------------- fonts
bash "$SAKTI_ROOT_DIR/scripts/install-fonts.sh"

# ----------------------------------------------------------- icons
bash "$SAKTI_ROOT_DIR/scripts/install-icons.sh"

# --------------------------------------------------- default mode
if [[ -x "$SAKTI_ROOT_DIR/desktop/mode_engine.py" ]]; then
  log_info "Applying default workspace mode"
  python3 "$SAKTI_ROOT_DIR/desktop/mode_engine.py" switch default || \
    log_warn "Mode apply incomplete (Plasma not running?)"
fi

# ------------------------------------------------------ KDE globals
mkdir -p "$HOME/.config"
kwriteconfig5 --file kwinrc --group Compositing --key Backend OpenGL
kwriteconfig5 --file kwinrc --group Effects --key BlurEnabled true
kwriteconfig5 --file kwinrc --group Effects --key BackgroundContrastEnabled true
kwriteconfig5 --file plasmarc --group Theme --key name Sakti

# Fonts (KDE)
kwriteconfig5 --file kdeglobals --group General --key font "Inter,10,-1,5,50,0,0,0,0,0"
kwriteconfig5 --file kdeglobals --group General --key fixed "JetBrains Mono,10,-1,5,50,0,0,0,0,0"

# Smooth animations
kwriteconfig5 --file kdeglobals --group KDE --key AnimationDurationFactor 1.0

log_ok "User shell configuration applied"

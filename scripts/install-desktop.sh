#!/usr/bin/env bash
# SaktiLinux AI — Desktop Experience Installer (Phase 2)
# Installs themes, plasmoids, icons, fonts, SDDM theme, and shell config.
# Idempotent. Safe to re-run.
#
# Usage: sudo bash scripts/install-desktop.sh
#        (installs system-wide; user config applied for the invoking user)

set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common/lib.sh"

require_root
require_command python3

DESKTOP_DIR="$SAKTI_ROOT_DIR/desktop"
THEMES_DIR="$SAKTI_ROOT_DIR/themes"
PLASMOIDS_DIR="$DESKTOP_DIR/plasmoids"
SDDM_THEME_DIR="$THEMES_DIR/sddm/sakti-login"

SYSTEM_DATA="/usr/share"
USER="${SUDO_USER:-$USER}"

log_info "SaktiLinux AI desktop installer starting"

# --------------------------------------------------------- packages
log_info "Installing desktop packages"
pacman -S --needed --noconfirm \
  plasma plasma-wayland-session \
  sddm \
  python \
  kvantum \
  breeze-icons \
  ttf-jetbrains-mono || log_warn "Some desktop packages failed (check mirror/repo)"

# ------------------------------------------------------- generate themes
log_info "Generating color schemes + Plasma theme from brand tokens"
python3 "$THEMES_DIR/generate.py" --output-dir "$THEMES_DIR"

log_info "Installing color schemes"
mkdir -p "$SYSTEM_DATA/color-schemes"
cp "$THEMES_DIR"/color-schemes/*.colors "$SYSTEM_DATA/color-schemes/"

log_info "Installing Plasma theme + splash"
mkdir -p "$SYSTEM_DATA/plasma/look-and-feel"
cp -r "$THEMES_DIR/plasma" "$SYSTEM_DATA/plasma/desktoptheme/Sakti"
cp -r "$THEMES_DIR/splash" "$SYSTEM_DATA/plasma/look-and-feel/SaktiSplash"

# --------------------------------------------------------- plasmoids
log_info "Installing Sakti plasmoids"
for plasmoid in "$PLASMOIDS_DIR"/*/; do
  name="$(basename "$plasmoid")"
  [[ -f "$plasmoid/metadata.json" ]] || continue
  log_info "  installing plasmoid: $name"
  install -d -o "$USER" -g "$USER" \
    "$SYSTEM_DATA/plasma/plasmoids/$name"
  cp -r "$plasmoid/." "$SYSTEM_DATA/plasma/plasmoids/$name/"
done

# ------------------------------------------------------------ SDDM
log_info "Installing SDDM login theme"
install -d -o "$USER" -g "$USER" "$SYSTEM_DATA/sddm/themes/sakti-login"
cp -r "$SDDM_THEME_DIR/." "$SYSTEM_DATA/sddm/themes/sakti-login/"

log_info "Configuring SDDM"
SDDM_CONF="/etc/sddm.conf.d/sakti.conf"
mkdir -p /etc/sddm.conf.d
cat > "$SDDM_CONF" <<EOF
[Theme]
Current=sakti-login

[General]
HaltCommand=/usr/bin/systemctl poweroff
RebootCommand=/usr/bin/systemctl reboot
EOF

# --------------------------------------------------------- user config
log_info "Installing mode engine + CLI"
install -d "$SYSTEM_DATA/sakti/desktop" "$SYSTEM_DATA/sakti/themes"
install -d "$SYSTEM_DATA/sakti/assets/wallpapers"
cp -r "$DESKTOP_DIR/modes" "$SYSTEM_DATA/sakti/desktop/modes"
cp "$DESKTOP_DIR/mode_engine.py" "$SYSTEM_DATA/sakti/desktop/"
cp "$DESKTOP_DIR/schema.py" "$SYSTEM_DATA/sakti/desktop/"
cp -r "$THEMES_DIR/color-schemes" "$SYSTEM_DATA/sakti/themes/"
cp -r "$SAKTI_ROOT_DIR/assets/wallpapers/." "$SYSTEM_DATA/sakti/assets/wallpapers/"
install -m 0755 "$SAKTI_ROOT_DIR/scripts/sakti-modes" "$SYSTEM_DATA/local/bin/sakti-modes"

# --------------------------------------------------------- user config
log_info "Applying user shell config for $USER"
runuser -u "$USER" -- bash "$SAKTI_ROOT_DIR/scripts/apply-user-shell.sh" || \
  log_warn "apply-user-shell.sh failed for $USER"

# ------------------------------------------------------------- done
log_ok "Desktop experience installed."
log_warn "Restart SDDM or reboot: sudo systemctl restart sddm"

#!/usr/bin/env bash
# SaktiLinux AI — Font Awesome style SVG icon theme installer
# Builds the SaktiIcons theme from assets/icons/*.svg into
# ~/.local/share/icons/SaktiIcons and refreshes the cache.

set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common/lib.sh"

ASSETS_DIR="$SAKTI_ROOT_DIR/assets/icons"
DEST_DIR="$HOME/.local/share/icons/SaktiIcons"

log_info "Installing SaktiIcons theme -> $DEST_DIR"
mkdir -p "$DEST_DIR"

# ---------------------------------------------------------- index.theme
cat > "$DEST_DIR/index.theme" <<'EOF'
[Icon Theme]
Name=SaktiIcons
Comment=Font Awesome style SVG icons for SaktiLinux AI
Inherits=breeze,hicolor
Directories=apps,actions,places,status
Example=preferences-desktop

[apps]
Size=48
Type=Scalable
MinSize=16
MaxSize=512

[actions]
Size=22
Type=Scalable
MinSize=16
MaxSize=512

[places]
Size=22
Type=Scalable
MinSize=16
MaxSize=512

[status]
Size=22
Type=Scalable
MinSize=16
MaxSize=512
EOF

# ------------------------------------------------------------- SVG sets
installed=0
for category in apps actions places status; do
  src_dir="$ASSETS_DIR/$category"
  [[ -d "$src_dir" ]] || continue
  mkdir -p "$DEST_DIR/$category"
  for svg in "$src_dir"/*.svg; do
    [[ -f "$svg" ]] || continue
    cp "$svg" "$DEST_DIR/$category/"
    installed=$((installed + 1))
  done
done

log_ok "Installed $installed SVG icons"

# --------------------------------------------------------------- cache
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -f -q "$DEST_DIR" || true
  log_ok "Icon cache refreshed"
fi

log_ok "SaktiIcons theme installed"

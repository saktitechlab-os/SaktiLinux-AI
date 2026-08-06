#!/usr/bin/env bash
# SaktiLinux AI — font installer (Inter, JetBrains Mono, Geist)
# Usage: bash scripts/install-fonts.sh
# Runs as current user; system fonts installed via sudo when needed.

set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common/lib.sh"

GEIST_VERSION="1.4.0"
GEIST_URL="https://github.com/vercel/geist-font/releases/download/${GEIST_VERSION}/geist.zip"
FONT_DIR="$HOME/.local/share/fonts"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

log_info "Installing fonts to $FONT_DIR"

# ------------------------------------------------------------ system
if command -v pacman >/dev/null 2>&1; then
  log_info "Installing Inter + JetBrains Mono via pacman"
  sudo pacman -S --needed --noconfirm inter-font ttf-jetbrains-mono
fi

# ------------------------------------------------------------- Geist
log_info "Downloading Geist $GEIST_VERSION"
if command -v curl >/dev/null 2>&1; then
  curl -fL --retry 3 -o "$TMP_DIR/geist.zip" "$GEIST_URL"
else
  wget -q "$GEIST_URL" -O "$TMP_DIR/geist.zip"
fi

mkdir -p "$FONT_DIR" "$TMP_DIR/geist"
unzip -q "$TMP_DIR/geist.zip" -d "$TMP_DIR/geist"

count=0
while IFS= read -r -d '' fontfile; do
  cp "$fontfile" "$FONT_DIR/"
  count=$((count + 1))
done < <(find "$TMP_DIR/geist" -type f \( -name "*.otf" -o -name "*.ttf" \) -print0)

log_ok "Installed $count Geist font files"

# -------------------------------------------------------------- cache
if command -v fc-cache >/dev/null 2>&1; then
  fc-cache -f "$FONT_DIR" >/dev/null
  log_ok "Font cache refreshed"
fi

log_ok "Fonts ready: Inter, JetBrains Mono, Geist"

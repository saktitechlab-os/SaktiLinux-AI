#!/usr/bin/env bash
# SaktiLinux AI — Base System Bootstrap (Phase 1)
# Idempotent. Safe to re-run. Must be run as root on Arch Linux.
#
# Usage: sudo bash scripts/bootstrap-base.sh [--with-dev]

set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common/lib.sh"

require_root
require_command pacman

WITH_DEV=false
[[ "${1:-}" == "--with-dev" ]] && WITH_DEV=true

log_info "SaktiLinux AI base bootstrap starting (with-dev=$WITH_DEV)"

# ---------------------------------------------------------------- locale
log_info "Configuring locale (en_US.UTF-8)"
sed -i 's/^#en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen
locale-gen >/dev/null

# ------------------------------------------------------------- pacman
log_info "Configuring pacman"
if ! grep -q "^ParallelDownloads" /etc/pacman.conf; then
  sed -i 's/^#ParallelDownloads = 5/ParallelDownloads = 8/' /etc/pacman.conf
fi
if ! grep -q "^Color" /etc/pacman.conf; then
  sed -i 's/^#Color/Color/' /etc/pacman.conf
fi
if ! grep -q "^ILoveCandy" /etc/pacman.conf; then
  sed -i '/^Color/a ILoveCandy' /etc/pacman.conf
fi

log_info "Syncing package databases"
pacman -Sy --noconfirm >/dev/null

# ---------------------------------------------------------- manifests
log_info "Installing base package manifest"
install_manifest "$SAKTI_ROOT_DIR/packages/lists/base.txt"
if $WITH_DEV; then
  log_info "Installing developer package manifest"
  install_manifest "$SAKTI_ROOT_DIR/packages/lists/dev.txt"
fi

# ------------------------------------------------------------ services
log_info "Configuring base services"
enable_service NetworkManager
enable_service systemd-resolved
enable_service systemd-timesyncd

log_info "Enabling SSH (dev convenience)"
systemctl enable --now sshd 2>/dev/null || log_warn "sshd not installed yet"

# ------------------------------------------------------ user / groups
SAKTI_USER="${SUDO_USER:-sakti}"
if ! id -u "$SAKTI_USER" >/dev/null 2>&1; then
  log_info "Creating user '$SAKTI_USER'"
  useradd -m -G wheel,storage,power -s /bin/bash "$SAKTI_USER"
fi
log_info "User '$SAKTI_USER' ready"

# --------------------------------------------------------------- skel
log_info "Creating user directory skeleton"
for d in Documents Downloads Projects Workspaces; do
  install -d -o "$SAKTI_USER" -g "$SAKTI_USER" "/home/$SAKTI_USER/$d"
done

# ------------------------------------------------------------- done
log_ok "Base bootstrap complete."
$WITH_DEV && log_ok "Developer tools installed."
log_warn "Reboot recommended: sudo reboot"
#!/usr/bin/env bash
# SaktiLinux AI — shared shell library
# Usage: source scripts/common/lib.sh

set -Eeuo pipefail

SAKTI_COLOR_RESET="\033[0m"
SAKTI_COLOR_CYAN="\033[0;36m"
SAKTI_COLOR_GREEN="\033[0;32m"
SAKTI_COLOR_YELLOW="\033[0;33m"
SAKTI_COLOR_RED="\033[0;31m"

SAKTI_ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SAKTI_OS_ID="saktilinux"

log_info()  { echo -e "${SAKTI_COLOR_CYAN}[sakti]${SAKTI_COLOR_RESET} $*"; }
log_ok()    { echo -e "${SAKTI_COLOR_GREEN}[ok]${SAKTI_COLOR_RESET} $*"; }
log_warn()  { echo -e "${SAKTI_COLOR_YELLOW}[warn]${SAKTI_COLOR_RESET} $*" >&2; }
log_error() { echo -e "${SAKTI_COLOR_RED}[error]${SAKTI_COLOR_RESET} $*" >&2; }

die() {
  log_error "$*"
  exit 1
}

require_root() {
  [[ "$(id -u)" -eq 0 ]] || die "This script must be run as root."
}

require_command() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1 || die "Required command not found: $cmd"
}

# Installs packages from a manifest line-by-line (supports # comments).
install_manifest() {
  local manifest="$1"
  [[ -f "$manifest" ]] || die "Package manifest not found: $manifest"
  local packages=()
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%%#*}"          # strip comments
    line="${line//[[:space:]]/}" # strip whitespace
    [[ -n "$line" ]] && packages+=("$line")
  done < "$manifest"
  if [[ "${#packages[@]}" -gt 0 ]]; then
    log_info "Installing ${#packages[@]} packages from $(basename "$manifest")"
    pacman -S --needed --noconfirm "${packages[@]}"
    log_ok "Installed $(basename "$manifest")"
  fi
}

is_systemd_active() {
  local unit="$1"
  systemctl is-active --quiet "$unit" 2>/dev/null
}

enable_service() {
  local unit="$1"
  if ! is_systemd_active "$unit"; then
    log_info "Enabling service: $unit"
    systemctl enable --now "$unit" || log_warn "Failed to enable $unit"
  else
    log_ok "Service already active: $unit"
  fi
}

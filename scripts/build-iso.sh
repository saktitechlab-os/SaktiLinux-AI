#!/usr/bin/env bash
# SaktiLinux AI — ISO Build Pipeline (Phase 15 stub wiring)
# Produces a reproducible live ISO from the phase manifests.
#
# NOTE: Full ISO builder lands in Phase 15. This file currently validates
# the required tooling and manifest integrity so the pipeline doesn't rot.

set -Eeuo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common/lib.sh"

require_command git
require_command pacman
if ! command -v mkarchiso >/dev/null 2>&1; then
  log_warn "archiso not installed — full ISO builder arrives in Phase 15"
fi

log_info "SaktiLinux AI ISO pipeline (Phase 1 placeholder-integrity check)"
log_info "Validating manifests..."
for manifest in "$SAKTI_ROOT_DIR"/packages/lists/*.txt; do
  [[ -f "$manifest" ]] || continue
  python3 "$SAKTI_ROOT_DIR/tests/unit/test_packages.py" "$manifest" || die "Invalid manifest: $manifest"
  log_ok "Validated: $(basename "$manifest")"
done
log_ok "Manifests OK. Full ISO builder arrives in Phase 15."
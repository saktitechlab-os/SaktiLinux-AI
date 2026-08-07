#!/usr/bin/env bash
# SaktiLinux AI — test runner
# Usage: bash tests/run-tests.sh

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
FAILURES=0

run() {
  echo "==> $*"
  if ! bash -c "$*"; then
    echo "FAILED: $*"
    FAILURES=1
  fi
}

echo "SaktiLinux AI test suite"
echo "========================"

run "python3 $ROOT_DIR/tests/unit/test_structure.py"
run "python3 $ROOT_DIR/tests/unit/test_packages.py $ROOT_DIR/packages/lists"
run "python3 $ROOT_DIR/tests/unit/test_desktop.py"

# Phase 3 — AI Brain
run "python3 -m unittest discover -s $ROOT_DIR/ai/tests/unit"
run "python3 -m unittest discover -s $ROOT_DIR/ai/tests/integration"

# Shell syntax check for all scripts
for script in "$ROOT_DIR"/scripts/*.sh "$ROOT_DIR"/scripts/common/*.sh; do
  [[ -f "$script" ]] || continue
  run "bash -n $script"
done

echo "========================"
if [[ "$FAILURES" -eq 0 ]]; then
  echo "All tests passed."
else
  echo "Some tests failed."
  exit 1
fi

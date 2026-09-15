#!/usr/bin/env bash
set -euo pipefail
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
: "${VEIR_DIR:?Set VEIR_DIR to the built VeIR checkout with --json interpreter support}"
cd "$REPO_DIR"
exec python3 -m veir_suite run --veir "$VEIR_DIR" --profile "${VEIR_PROFILE:-local}" --reference-revision "${LLVM_REVISION:-unknown}" "$@"

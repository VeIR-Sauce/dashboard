#!/usr/bin/env bash
set -euo pipefail
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VEIR_BUILD_DIR="${1:?Provide an isolated VeIR checkout directory}"
VEIR_REVISION="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["veir_base_revision"])' "$REPO_DIR/profiles/ci.json")"
if [[ -e "$VEIR_BUILD_DIR" ]]; then
  echo "Refusing to replace an existing checkout: $VEIR_BUILD_DIR" >&2
  exit 2
fi
git init "$VEIR_BUILD_DIR"
git -C "$VEIR_BUILD_DIR" remote add origin https://github.com/opencompl/veir.git
git -C "$VEIR_BUILD_DIR" fetch --depth=1 origin "$VEIR_REVISION"
git -C "$VEIR_BUILD_DIR" checkout --detach "$VEIR_REVISION"
git -C "$VEIR_BUILD_DIR" submodule update --init --recursive
git -C "$VEIR_BUILD_DIR" apply --check "$REPO_DIR/integrations/veir-test-instrumentation.patch"
git -C "$VEIR_BUILD_DIR" apply "$REPO_DIR/integrations/veir-test-instrumentation.patch"
echo "Prepared pinned VeIR plus the recorded instrumentation patch at $VEIR_BUILD_DIR"

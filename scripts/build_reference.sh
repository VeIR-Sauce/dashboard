#!/usr/bin/env bash
# For an isolated CI runner. On the shared workstation, wrap in agent-scoped.
set -euo pipefail
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REF_DIR="${1:?Provide an isolated reference build directory}"
LLVM_REVISION="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["llvm_revision"])' "$REPO_DIR/profiles/ci.json")"
mkdir -p "$REF_DIR"
REF_DIR="$(cd "$REF_DIR" && pwd)"
if [[ -f "$REF_DIR/revision" ]] && [[ "$(cat "$REF_DIR/revision")" == "$LLVM_REVISION" ]]; then
  for tool in mlir-opt mlir-translate lli opt FileCheck split-file; do
    test -x "$REF_DIR/bin/$tool"
  done
  exit 0
fi
if [[ ! -d "$REF_DIR/src/.git" ]]; then
  git init "$REF_DIR/src"
  git -C "$REF_DIR/src" remote add origin https://github.com/llvm/llvm-project.git
fi
git -C "$REF_DIR/src" fetch --depth=1 origin "$LLVM_REVISION"
git -C "$REF_DIR/src" checkout --detach "$LLVM_REVISION"
cmake -G Ninja -S "$REF_DIR/src/llvm" -B "$REF_DIR/build" \
  -DCMAKE_BUILD_TYPE=Release -DLLVM_ENABLE_PROJECTS=mlir -DLLVM_TARGETS_TO_BUILD=Native \
  -DLLVM_ENABLE_ASSERTIONS=OFF -DLLVM_INCLUDE_TESTS=OFF -DLLVM_BUILD_UTILS=ON \
  -DLLVM_ENABLE_BINDINGS=OFF -DLLVM_ENABLE_TERMINFO=OFF \
  -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ -DLLVM_USE_LINKER=lld
cmake --build "$REF_DIR/build" --target mlir-opt mlir-translate lli opt FileCheck split-file --parallel "${BUILD_JOBS:-2}"
mkdir -p "$REF_DIR/bin"
for tool in mlir-opt mlir-translate lli opt FileCheck split-file; do
  cp "$REF_DIR/build/bin/$tool" "$REF_DIR/bin/$tool"
done
printf '%s\n' "$LLVM_REVISION" > "$REF_DIR/revision"

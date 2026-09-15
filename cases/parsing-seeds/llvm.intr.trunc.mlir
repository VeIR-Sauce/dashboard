// A scalar parsing example, validated by the pinned MLIR verifier.
module {
  llvm.func @sample(%arg0: f32) {
    %0 = "llvm.intr.trunc"(%arg0) : (f32) -> f32
    llvm.return
  }
}

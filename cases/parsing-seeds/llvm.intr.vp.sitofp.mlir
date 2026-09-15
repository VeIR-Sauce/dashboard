// A vector-predicated conversion, validated by the pinned MLIR verifier.
module {
  llvm.func @sample(%arg0: vector<8xi64>, %mask: vector<8xi1>, %length: i32) {
    %0 = "llvm.intr.vp.sitofp"(%arg0, %mask, %length) : (vector<8xi64>, vector<8xi1>, i32) -> vector<8xf64>
    llvm.return
  }
}

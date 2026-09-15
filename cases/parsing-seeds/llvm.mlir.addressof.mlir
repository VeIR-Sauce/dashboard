module {
  llvm.mlir.global external @value() : i32
  llvm.func @sample() {
    %0 = llvm.mlir.addressof @value : !llvm.ptr
    llvm.return
  }
}

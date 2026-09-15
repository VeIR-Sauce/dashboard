module {
  llvm.func @sample(%condition: i1) {
    llvm.cond_br %condition, ^yes, ^no
  ^yes:
    llvm.return
  ^no:
    llvm.return
  }
}

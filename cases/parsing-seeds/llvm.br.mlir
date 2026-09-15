module {
  llvm.func @sample() {
    llvm.br ^exit
  ^exit:
    llvm.return
  }
}

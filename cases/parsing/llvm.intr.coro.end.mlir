"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (ptr, i1)>, linkage = #llvm.linkage<external>, sym_name = "coro_end", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: !llvm.ptr, %arg1: i1):
    %0 = "llvm.mlir.none"() : () -> token
    %1 = "llvm.intr.coro.end"(%arg0, %arg1, %0) : (!llvm.ptr, i1, token) -> !llvm.void
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

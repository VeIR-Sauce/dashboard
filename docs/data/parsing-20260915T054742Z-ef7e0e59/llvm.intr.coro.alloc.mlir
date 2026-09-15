"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void ()>, linkage = #llvm.linkage<external>, sym_name = "coro_alloc", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
    %0 = "llvm.mlir.constant"() <{value = 0 : i32}> : () -> i32
    %1 = "llvm.mlir.zero"() : () -> !llvm.ptr
    %2 = "llvm.intr.coro.id"(%0, %1, %1, %1) : (i32, !llvm.ptr, !llvm.ptr, !llvm.ptr) -> token
    %3 = "llvm.intr.coro.alloc"(%2) : (token) -> i1
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

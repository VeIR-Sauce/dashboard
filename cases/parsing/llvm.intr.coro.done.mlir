"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (ptr)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: !llvm.ptr):
    %0 = "llvm.intr.coro.done"(%arg0) : (!llvm.ptr) -> i1
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (i32, ptr, ptr, ptr)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: i32, %arg1: !llvm.ptr, %arg2: !llvm.ptr, %arg3: !llvm.ptr):
    %0 = "llvm.intr.coro.id"(%arg0, %arg1, %arg2, %arg3) : (i32, !llvm.ptr, !llvm.ptr, !llvm.ptr) -> token
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (i16, ptr, ptr, i32)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: i16, %arg1: !llvm.ptr, %arg2: !llvm.ptr, %arg3: i32):
    %0 = "llvm.intr.annotation"(%arg0, %arg1, %arg2, %arg3) : (i16, !llvm.ptr, !llvm.ptr, i32) -> i16
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

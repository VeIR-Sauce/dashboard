"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (i32, i32, i32)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: i32, %arg1: i32, %arg2: i32):
    %0 = "llvm.intr.fshl"(%arg0, %arg1, %arg2) : (i32, i32, i32) -> i32
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

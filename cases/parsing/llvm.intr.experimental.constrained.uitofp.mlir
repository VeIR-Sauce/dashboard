"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (i32)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: i32):
    %0 = "llvm.intr.experimental.constrained.uitofp"(%arg0) <{fastmathFlags = #llvm.fastmath<none>, fpExceptionBehavior = 0 : i64, roundingmode = 0 : i64}> : (i32) -> f32
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (f32)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: f32):
    %0 = "llvm.intr.experimental.constrained.fptosi"(%arg0) <{fastmathFlags = #llvm.fastmath<none>, fpExceptionBehavior = 2 : i64}> : (f32) -> i32
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

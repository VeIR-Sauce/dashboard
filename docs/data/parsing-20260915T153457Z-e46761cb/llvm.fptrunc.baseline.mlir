"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (f64)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: f64):
    %0 = "llvm.fptrunc"(%arg0) <{fastmathFlags = #llvm.fastmath<none>}> : (f64) -> f32
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

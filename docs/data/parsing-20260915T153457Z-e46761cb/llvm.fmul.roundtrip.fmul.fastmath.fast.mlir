"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<f64 (f64, f64)>, linkage = #llvm.linkage<external>, sym_name = "main", visibility_ = 0 : i64}> ({
  ^bb0(%arg0: f64, %arg1: f64):
    %0 = "llvm.fmul"(%arg0, %arg1) <{fastmathFlags = #llvm.fastmath<fast>}> : (f64, f64) -> f64
    "llvm.return"(%0) : (f64) -> ()
  }) : () -> ()
}) : () -> ()

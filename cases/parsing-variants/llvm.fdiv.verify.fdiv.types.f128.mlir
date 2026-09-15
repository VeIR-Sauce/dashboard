"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<f128 (f128, f128)>, linkage = #llvm.linkage<external>, sym_name = "main", visibility_ = 0 : i64}> ({
  ^bb0(%arg0: f128, %arg1: f128):
    %0 = "llvm.fdiv"(%arg0, %arg1) <{fastmathFlags = #llvm.fastmath<none>}> : (f128, f128) -> f128
    "llvm.return"(%0) : (f128) -> ()
  }) : () -> ()
}) : () -> ()

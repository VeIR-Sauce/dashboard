"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (vector<4xf32>, vector<4xf32>)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: vector<4xf32>, %arg1: vector<4xf32>):
    %0 = "llvm.intr.experimental.constrained.fcmps"(%arg0, %arg1) <{fastmathFlags = #llvm.fastmath<none>, fpExceptionBehavior = 0 : i64, predicate = 4 : i64}> : (vector<4xf32>, vector<4xf32>) -> vector<4xi1>
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

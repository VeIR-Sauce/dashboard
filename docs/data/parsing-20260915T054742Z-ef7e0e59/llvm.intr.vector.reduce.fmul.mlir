"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (f32, vector<8xf32>)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: f32, %arg1: vector<8xf32>):
    %0 = "llvm.intr.vector.reduce.fmul"(%arg0, %arg1) <{fastmathFlags = #llvm.fastmath<none>}> : (f32, vector<8xf32>) -> f32
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (vector<4xf64>)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: vector<4xf64>):
    %0 = "llvm.intr.vector.deinterleave2"(%arg0) : (vector<4xf64>) -> !llvm.struct<(vector<2xf64>, vector<2xf64>)>
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

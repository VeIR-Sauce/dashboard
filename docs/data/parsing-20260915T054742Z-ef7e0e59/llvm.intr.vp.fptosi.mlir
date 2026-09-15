"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (vector<8xf64>, vector<8xi1>, i32)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: vector<8xf64>, %arg1: vector<8xi1>, %arg2: i32):
    %0 = "llvm.intr.vp.fptosi"(%arg0, %arg1, %arg2) : (vector<8xf64>, vector<8xi1>, i32) -> vector<8xi64>
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

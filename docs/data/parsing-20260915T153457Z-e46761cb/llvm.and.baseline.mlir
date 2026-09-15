"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (vector<4xi64>, vector<4xi64>)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: vector<4xi64>, %arg1: vector<4xi64>):
    %0 = "llvm.and"(%arg0, %arg1) : (vector<4xi64>, vector<4xi64>) -> vector<4xi64>
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

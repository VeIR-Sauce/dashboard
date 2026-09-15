"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (vector<4xf32>, vector<4xf32>)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: vector<4xf32>, %arg1: vector<4xf32>):
    %0 = "llvm.shufflevector"(%arg0, %arg1) <{mask = array<i32: 0, 0, 0, 0, 7>}> : (vector<4xf32>, vector<4xf32>) -> vector<5xf32>
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

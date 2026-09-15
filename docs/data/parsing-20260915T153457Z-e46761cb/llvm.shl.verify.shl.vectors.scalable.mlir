"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<vector<[4]xi32> (vector<[4]xi32>, vector<[4]xi32>)>, linkage = #llvm.linkage<external>, sym_name = "main", visibility_ = 0 : i64}> ({
  ^bb0(%arg0: vector<[4]xi32>, %arg1: vector<[4]xi32>):
    %0 = "llvm.shl"(%arg0, %arg1) <{overflowFlags = 0 : i32}> : (vector<[4]xi32>, vector<[4]xi32>) -> vector<[4]xi32>
    "llvm.return"(%0) : (vector<[4]xi32>) -> ()
  }) : () -> ()
}) : () -> ()

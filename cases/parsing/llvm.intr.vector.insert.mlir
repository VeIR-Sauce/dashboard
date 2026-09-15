"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (vector<[4]xi32>, vector<8xi32>)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: vector<[4]xi32>, %arg1: vector<8xi32>):
    %0 = "llvm.intr.vector.insert"(%arg0, %arg1) <{pos = 0 : i64}> : (vector<[4]xi32>, vector<8xi32>) -> vector<[4]xi32>
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

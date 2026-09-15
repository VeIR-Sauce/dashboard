"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (vector<8xi32>)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: vector<8xi32>):
    %0 = "llvm.intr.vector.reduce.umin"(%arg0) : (vector<8xi32>) -> i32
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

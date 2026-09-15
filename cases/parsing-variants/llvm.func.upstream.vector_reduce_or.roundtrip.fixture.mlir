"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (vector<4xi8>, vector<2xi32>, vector<8xi1>)>, linkage = #llvm.linkage<external>, sym_name = "reduce", visibility_ = 0 : i64}> ({
  ^bb0(%arg0: vector<4xi8>, %arg1: vector<2xi32>, %arg2: vector<8xi1>):
    %0 = "llvm.intr.vector.reduce.or"(%arg0) : (vector<4xi8>) -> i8
    %1 = "llvm.intr.vector.reduce.or"(%arg1) : (vector<2xi32>) -> i32
    %2 = "llvm.intr.vector.reduce.or"(%arg2) : (vector<8xi1>) -> i1
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

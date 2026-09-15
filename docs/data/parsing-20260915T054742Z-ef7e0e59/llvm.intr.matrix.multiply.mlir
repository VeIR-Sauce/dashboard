"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (vector<64xf32>, vector<48xf32>)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: vector<64xf32>, %arg1: vector<48xf32>):
    %0 = "llvm.intr.matrix.multiply"(%arg0, %arg1) <{lhs_columns = 16 : i32, lhs_rows = 4 : i32, rhs_columns = 3 : i32}> : (vector<64xf32>, vector<48xf32>) -> vector<12xf32>
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

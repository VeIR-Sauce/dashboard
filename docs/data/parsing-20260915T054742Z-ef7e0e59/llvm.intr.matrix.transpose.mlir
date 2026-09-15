"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (vector<48xf32>)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: vector<48xf32>):
    %0 = "llvm.intr.matrix.transpose"(%arg0) <{columns = 16 : i32, rows = 3 : i32}> : (vector<48xf32>) -> vector<48xf32>
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

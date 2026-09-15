"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (vector<48xf32>, ptr, i64)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: vector<48xf32>, %arg1: !llvm.ptr, %arg2: i64):
    "llvm.intr.matrix.column.major.store"(%arg0, %arg1, %arg2) <{columns = 16 : i32, isVolatile = false, rows = 3 : i32}> : (vector<48xf32>, !llvm.ptr, i64) -> ()
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

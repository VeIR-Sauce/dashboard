"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (ptr, i64)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: !llvm.ptr, %arg1: i64):
    %0 = "llvm.intr.matrix.column.major.load"(%arg0, %arg1) <{columns = 16 : i32, isVolatile = false, rows = 3 : i32}> : (!llvm.ptr, i64) -> vector<48xf32>
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

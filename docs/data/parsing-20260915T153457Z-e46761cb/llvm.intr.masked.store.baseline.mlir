"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (vector<7xf32>, ptr, vector<7xi1>)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: vector<7xf32>, %arg1: !llvm.ptr, %arg2: vector<7xi1>):
    "llvm.intr.masked.store"(%arg0, %arg1, %arg2) <{alignment = 1 : i32}> : (vector<7xf32>, !llvm.ptr, vector<7xi1>) -> ()
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

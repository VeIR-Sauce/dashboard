"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (vector<8xi32>, ptr, vector<8xi1>, i32)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: vector<8xi32>, %arg1: !llvm.ptr, %arg2: vector<8xi1>, %arg3: i32):
    "llvm.intr.vp.store"(%arg0, %arg1, %arg2, %arg3) : (vector<8xi32>, !llvm.ptr, vector<8xi1>, i32) -> ()
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

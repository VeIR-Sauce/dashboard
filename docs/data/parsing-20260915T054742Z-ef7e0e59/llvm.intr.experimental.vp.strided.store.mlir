"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (vector<8xi32>, ptr, i32, vector<8xi1>, i32)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: vector<8xi32>, %arg1: !llvm.ptr, %arg2: i32, %arg3: vector<8xi1>, %arg4: i32):
    "llvm.intr.experimental.vp.strided.store"(%arg0, %arg1, %arg2, %arg3, %arg4) : (vector<8xi32>, !llvm.ptr, i32, vector<8xi1>, i32) -> ()
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

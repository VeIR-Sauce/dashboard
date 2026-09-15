"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (ptr, i32, vector<8xi1>, i32)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: !llvm.ptr, %arg1: i32, %arg2: vector<8xi1>, %arg3: i32):
    %0 = "llvm.intr.experimental.vp.strided.load"(%arg0, %arg1, %arg2, %arg3) : (!llvm.ptr, i32, vector<8xi1>, i32) -> vector<8xi32>
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

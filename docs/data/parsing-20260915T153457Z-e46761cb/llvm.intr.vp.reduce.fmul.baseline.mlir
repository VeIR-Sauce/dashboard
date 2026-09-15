"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (f32, vector<8xf32>, vector<8xi1>, i32)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: f32, %arg1: vector<8xf32>, %arg2: vector<8xi1>, %arg3: i32):
    %0 = "llvm.intr.vp.reduce.fmul"(%arg0, %arg1, %arg2, %arg3) : (f32, vector<8xf32>, vector<8xi1>, i32) -> f32
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

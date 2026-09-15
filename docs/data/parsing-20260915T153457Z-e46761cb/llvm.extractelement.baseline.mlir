"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (vector<4xf32>, i32)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: vector<4xf32>, %arg1: i32):
    %0 = "llvm.extractelement"(%arg0, %arg1) : (vector<4xf32>, i32) -> f32
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

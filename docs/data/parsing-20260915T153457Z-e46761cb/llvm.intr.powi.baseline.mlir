"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (f32, i32)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: f32, %arg1: i32):
    %0 = "llvm.intr.powi"(%arg0, %arg1) <{fastmathFlags = #llvm.fastmath<fast>}> : (f32, i32) -> f32
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

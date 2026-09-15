"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (i16, i16)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: i16, %arg1: i16):
    %0 = "llvm.intr.expect.with.probability"(%arg0, %arg1) <{prob = 5.000000e-01 : f64}> : (i16, i16) -> i16
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (i64, i64)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: i64, %arg1: i64):
    %0 = "llvm.intr.get.active.lane.mask"(%arg0, %arg1) : (i64, i64) -> vector<7xi1>
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (i64)>, linkage = #llvm.linkage<external>, sym_name = "flags", visibility_ = 0 : i64}> ({
  ^bb0(%arg0: i64):
    %0 = "llvm.sdiv"(%arg0, %arg0) <{isExact}> : (i64, i64) -> i64
    %1 = "llvm.udiv"(%arg0, %arg0) <{isExact}> : (i64, i64) -> i64
    %2 = "llvm.lshr"(%arg0, %arg0) <{isExact}> : (i64, i64) -> i64
    %3 = "llvm.ashr"(%arg0, %arg0) <{isExact}> : (i64, i64) -> i64
    %4 = "llvm.or"(%arg0, %arg0) <{isDisjoint}> : (i64, i64) -> i64
    %5 = "llvm.sdiv"(%arg0, %arg0) : (i64, i64) -> i64
    %6 = "llvm.or"(%arg0, %arg0) : (i64, i64) -> i64
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

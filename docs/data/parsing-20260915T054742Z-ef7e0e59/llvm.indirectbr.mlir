"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<i32 (ptr, i32, i32)>, linkage = #llvm.linkage<external>, sym_name = "ib0", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: !llvm.ptr, %arg1: i32, %arg2: i32):
    "llvm.indirectbr"(%arg0, %arg1, %arg2, %arg1)[^bb1, ^bb2] <{indbr_operand_segments = array<i32: 1, 2>}> : (!llvm.ptr, i32, i32, i32) -> ()
  ^bb1(%0: i32):  // pred: ^bb0
    "llvm.return"(%0) : (i32) -> ()
  ^bb2(%1: i32, %2: i32):  // pred: ^bb0
    %3 = "llvm.add"(%1, %2) <{overflowFlags = 0 : i32}> : (i32, i32) -> i32
    "llvm.return"(%3) : (i32) -> ()
  }) : () -> ()
}) : () -> ()

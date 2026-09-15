"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (i1, ptr, i32)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: i1, %arg1: !llvm.ptr, %arg2: i32):
    "llvm.call_intrinsic"(%arg0, %arg1, %arg2) <{fastmathFlags = #llvm.fastmath<none>, intrin = "llvm.assume", op_bundle_sizes = array<i32: 2>, op_bundle_tags = ["align"], operandSegmentSizes = array<i32: 1, 2>}> : (i1, !llvm.ptr, i32) -> ()
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

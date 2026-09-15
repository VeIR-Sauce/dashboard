"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<i64 (ptr, i1)>, linkage = #llvm.linkage<external>, sym_name = "sizes", visibility_ = 0 : i64}> ({
  ^bb0(%arg0: !llvm.ptr, %arg1: i1):
    %0 = "llvm.call_intrinsic"(%arg0, %arg1, %arg1, %arg1) <{fastmathFlags = #llvm.fastmath<none>, intrin = "llvm.objectsize.i64.p0", op_bundle_sizes = array<i32>, operandSegmentSizes = array<i32: 4, 0>}> : (!llvm.ptr, i1, i1, i1) -> i64
    "llvm.call_intrinsic"() <{fastmathFlags = #llvm.fastmath<none>, intrin = "llvm.donothing", op_bundle_sizes = array<i32>, operandSegmentSizes = array<i32: 0, 0>}> : () -> ()
    "llvm.call_intrinsic"(%arg0, %arg1) <{fastmathFlags = #llvm.fastmath<none>, intrin = "llvm.assume", op_bundle_sizes = array<i32: 1>, op_bundle_tags = ["align"], operandSegmentSizes = array<i32: 1, 1>}> : (!llvm.ptr, i1) -> ()
    "llvm.return"(%0) : (i64) -> ()
  }) : () -> ()
}) : () -> ()

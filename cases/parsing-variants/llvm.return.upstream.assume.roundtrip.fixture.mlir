"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (i1, ptr)>, linkage = #llvm.linkage<external>, sym_name = "f", visibility_ = 0 : i64}> ({
  ^bb0(%arg0: i1, %arg1: !llvm.ptr):
    %0 = "llvm.mlir.constant"() <{value = true}> : () -> i1
    %1 = "llvm.mlir.constant"() <{value = 4 : i64}> : () -> i64
    "llvm.intr.assume"(%arg0) <{op_bundle_sizes = array<i32>}> : (i1) -> ()
    "llvm.intr.assume"(%0, %arg1, %1) <{op_bundle_sizes = array<i32: 2>, op_bundle_tags = ["align"]}> : (i1, !llvm.ptr, i64) -> ()
    "llvm.intr.assume"(%0, %arg1, %1, %arg1) <{op_bundle_sizes = array<i32: 2, 1>, op_bundle_tags = ["align", "nonnull"]}> : (i1, !llvm.ptr, i64, !llvm.ptr) -> ()
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

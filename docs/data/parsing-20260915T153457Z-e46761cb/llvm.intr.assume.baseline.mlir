"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (i1)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: i1):
    "llvm.intr.assume"(%arg0) <{op_bundle_sizes = array<i32>}> : (i1) -> ()
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

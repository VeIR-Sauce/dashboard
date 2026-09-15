"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void ()>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
    %0 = "llvm.intr.stepvector"() : () -> vector<[16]xi32>
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

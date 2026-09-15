"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void ()>, linkage = #llvm.linkage<external>, sym_name = "barriers", visibility_ = 0 : i64}> ({
    "llvm.fence"() <{ordering = 4 : i64}> : () -> ()
    "llvm.fence"() <{ordering = 5 : i64}> : () -> ()
    "llvm.fence"() <{ordering = 6 : i64}> : () -> ()
    "llvm.fence"() <{ordering = 7 : i64}> : () -> ()
    "llvm.fence"() <{ordering = 7 : i64, syncscope = "singlethread"}> : () -> ()
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

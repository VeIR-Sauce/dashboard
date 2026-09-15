"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<bf16 (bf16, bf16)>, linkage = #llvm.linkage<external>, sym_name = "main", visibility_ = 0 : i64}> ({
  ^bb0(%arg0: bf16, %arg1: bf16):
    %0 = "llvm.fsub"(%arg0, %arg1) <{fastmathFlags = #llvm.fastmath<none>}> : (bf16, bf16) -> bf16
    "llvm.return"(%0) : (bf16) -> ()
  }) : () -> ()
}) : () -> ()

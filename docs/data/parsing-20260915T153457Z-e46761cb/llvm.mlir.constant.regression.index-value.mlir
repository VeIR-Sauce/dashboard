"builtin.module"() ({
  "llvm.func"() <{sym_name = "sample", function_type = !llvm.func<void ()>}> ({
    %0 = "llvm.mlir.constant"() <{value = 1 : index}> : () -> i64
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

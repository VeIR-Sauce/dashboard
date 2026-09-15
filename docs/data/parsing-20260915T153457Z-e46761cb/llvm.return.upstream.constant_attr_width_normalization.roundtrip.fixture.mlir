"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void ()>, linkage = #llvm.linkage<external>, sym_name = "constants", visibility_ = 0 : i64}> ({
    %0 = "llvm.mlir.constant"() <{value = -56 : i8}> : () -> i32
    %1 = "llvm.mlir.constant"() <{value = -1 : i2}> : () -> i32
    %2 = "llvm.mlir.constant"() <{value = -1 : i32}> : () -> i64
    %3 = "llvm.mlir.constant"() <{value = true}> : () -> i32
    %4 = "llvm.mlir.constant"() <{value = -3 : i8}> : () -> i32
    %5 = "llvm.mlir.constant"() <{value = true}> : () -> i32
    %6 = "llvm.mlir.constant"() <{value = 300 : i32}> : () -> i8
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

"builtin.module"() ({
  "llvm.mlir.global"() <{addr_space = 0 : i32, global_type = !llvm.struct<(i16, i8)>, linkage = #llvm.linkage<external>, sym_name = "partly", tls_mode = 0 : i64, visibility_ = 0 : i64}> ({
    %2 = "llvm.mlir.undef"() : () -> !llvm.struct<(i16, i8)>
    "llvm.return"(%2) : (!llvm.struct<(i16, i8)>) -> ()
  }) : () -> ()
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<i32 ()>, linkage = #llvm.linkage<external>, sym_name = "scalar", visibility_ = 0 : i64}> ({
    %0 = "llvm.mlir.undef"() : () -> i32
    %1 = "llvm.mlir.undef"() : () -> !llvm.ptr
    "llvm.return"(%0) : (i32) -> ()
  }) : () -> ()
}) : () -> ()

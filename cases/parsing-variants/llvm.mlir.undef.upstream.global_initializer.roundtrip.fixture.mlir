"builtin.module"() ({
  "llvm.mlir.global"() <{addr_space = 0 : i32, alignment = 1 : i64, constant, dso_local, global_type = !llvm.array<1 x struct<"struct.et_info", (i8, i8)>>, linkage = #llvm.linkage<internal>, sym_name = "fmtinfo", tls_mode = 0 : i64, unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
    %0 = "llvm.mlir.constant"() <{value = 10 : i8}> : () -> i8
    %1 = "llvm.mlir.constant"() <{value = 114 : i8}> : () -> i8
    %2 = "llvm.mlir.undef"() : () -> !llvm.struct<"struct.et_info", (i8, i8)>
    %3 = "llvm.insertvalue"(%2, %1) <{position = array<i64: 0>}> : (!llvm.struct<"struct.et_info", (i8, i8)>, i8) -> !llvm.struct<"struct.et_info", (i8, i8)>
    %4 = "llvm.insertvalue"(%3, %0) <{position = array<i64: 1>}> : (!llvm.struct<"struct.et_info", (i8, i8)>, i8) -> !llvm.struct<"struct.et_info", (i8, i8)>
    %5 = "llvm.mlir.undef"() : () -> !llvm.array<1 x struct<"struct.et_info", (i8, i8)>>
    %6 = "llvm.insertvalue"(%5, %4) <{position = array<i64: 0>}> : (!llvm.array<1 x struct<"struct.et_info", (i8, i8)>>, !llvm.struct<"struct.et_info", (i8, i8)>) -> !llvm.array<1 x struct<"struct.et_info", (i8, i8)>>
    "llvm.return"(%6) : (!llvm.array<1 x struct<"struct.et_info", (i8, i8)>>) -> ()
  }) : () -> ()
}) : () -> ()

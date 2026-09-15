"builtin.module"() ({
  "llvm.mlir.global"() <{addr_space = 0 : i32, global_type = !llvm.array<2 x ptr>, linkage = #llvm.linkage<external>, sym_name = "table", tls_mode = 0 : i64, visibility_ = 0 : i64}> ({
    %6 = "llvm.mlir.undef"() : () -> !llvm.array<2 x ptr>
    %7 = "llvm.mlir.zero"() : () -> !llvm.ptr
    %8 = "llvm.insertvalue"(%6, %7) <{position = array<i64: 0>}> : (!llvm.array<2 x ptr>, !llvm.ptr) -> !llvm.array<2 x ptr>
    %9 = "llvm.insertvalue"(%8, %7) <{position = array<i64: 1>}> : (!llvm.array<2 x ptr>, !llvm.ptr) -> !llvm.array<2 x ptr>
    "llvm.return"(%9) : (!llvm.array<2 x ptr>) -> ()
  }) : () -> ()
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void ()>, linkage = #llvm.linkage<external>, sym_name = "nested", visibility_ = 0 : i64}> ({
    %0 = "llvm.mlir.undef"() : () -> !llvm.struct<(i32, struct<(i64, i8)>)>
    %1 = "llvm.mlir.constant"() <{value = 7 : i64}> : () -> i64
    %2 = "llvm.insertvalue"(%0, %1) <{position = array<i64: 1, 0>}> : (!llvm.struct<(i32, struct<(i64, i8)>)>, i64) -> !llvm.struct<(i32, struct<(i64, i8)>)>
    %3 = "llvm.insertvalue"(%0, %2) <{position = array<i64>}> : (!llvm.struct<(i32, struct<(i64, i8)>)>, !llvm.struct<(i32, struct<(i64, i8)>)>) -> !llvm.struct<(i32, struct<(i64, i8)>)>
    %4 = "llvm.mlir.undef"() : () -> !llvm.array<2 x struct<(i64, i8)>>
    %5 = "llvm.insertvalue"(%4, %1) <{position = array<i64: 1, 0>}> : (!llvm.array<2 x struct<(i64, i8)>>, i64) -> !llvm.array<2 x struct<(i64, i8)>>
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

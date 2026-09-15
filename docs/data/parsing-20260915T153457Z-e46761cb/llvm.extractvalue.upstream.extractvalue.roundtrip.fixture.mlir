"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<ptr (array<2 x ptr>)>, linkage = #llvm.linkage<external>, sym_name = "second", visibility_ = 0 : i64}> ({
  ^bb0(%arg0: !llvm.array<2 x ptr>):
    %5 = "llvm.extractvalue"(%arg0) <{position = array<i64: 0>}> : (!llvm.array<2 x ptr>) -> !llvm.ptr
    %6 = "llvm.extractvalue"(%arg0) <{position = array<i64: 1>}> : (!llvm.array<2 x ptr>) -> !llvm.ptr
    "llvm.return"(%6) : (!llvm.ptr) -> ()
  }) : () -> ()
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void ()>, linkage = #llvm.linkage<external>, sym_name = "nested", visibility_ = 0 : i64}> ({
    %0 = "llvm.mlir.undef"() : () -> !llvm.struct<(i32, struct<(i64, i8)>)>
    %1 = "llvm.extractvalue"(%0) <{position = array<i64: 1, 0>}> : (!llvm.struct<(i32, struct<(i64, i8)>)>) -> i64
    %2 = "llvm.extractvalue"(%0) <{position = array<i64>}> : (!llvm.struct<(i32, struct<(i64, i8)>)>) -> !llvm.struct<(i32, struct<(i64, i8)>)>
    %3 = "llvm.mlir.undef"() : () -> !llvm.array<2 x struct<(i64, i8)>>
    %4 = "llvm.extractvalue"(%3) <{position = array<i64: 1, 0>}> : (!llvm.array<2 x struct<(i64, i8)>>) -> i64
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (struct<(ptr)>, ptr)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: !llvm.struct<(ptr)>, %arg1: !llvm.ptr):
    %0 = "llvm.insertvalue"(%arg0, %arg1) <{position = array<i64: 0>}> : (!llvm.struct<(ptr)>, !llvm.ptr) -> !llvm.struct<(ptr)>
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

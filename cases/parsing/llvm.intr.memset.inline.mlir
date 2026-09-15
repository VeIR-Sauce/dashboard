"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (ptr, i8)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: !llvm.ptr, %arg1: i8):
    "llvm.intr.memset.inline"(%arg0, %arg1) <{arg_attrs = [{llvm.align = 8 : i64}, {}], isVolatile = true, len = 10 : i32}> : (!llvm.ptr, i8) -> ()
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

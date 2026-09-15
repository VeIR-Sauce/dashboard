"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (ptr)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: !llvm.ptr):
    %0 = "llvm.ptrtoaddr"(%arg0) : (!llvm.ptr) -> i64
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

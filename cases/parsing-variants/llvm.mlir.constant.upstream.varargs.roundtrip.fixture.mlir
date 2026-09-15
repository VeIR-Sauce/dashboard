"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<i32 (i32, ...)>, linkage = #llvm.linkage<external>, sym_name = "sum", visibility_ = 0 : i64}> ({
  ^bb0(%arg0: i32):
    %0 = "llvm.mlir.constant"() <{value = 1 : i64}> : () -> i64
    %1 = "llvm.alloca"(%0) <{alignment = 8 : i64, elem_type = !llvm.ptr}> : (i64) -> !llvm.ptr
    "llvm.intr.vastart"(%1) : (!llvm.ptr) -> ()
    %2 = "llvm.va_arg"(%1) : (!llvm.ptr) -> i32
    %3 = "llvm.va_arg"(%1) : (!llvm.ptr) -> f64
    %4 = "llvm.va_arg"(%1) : (!llvm.ptr) -> !llvm.ptr
    "llvm.intr.vaend"(%1) : (!llvm.ptr) -> ()
    "llvm.return"(%2) : (i32) -> ()
  }) : () -> ()
}) : () -> ()

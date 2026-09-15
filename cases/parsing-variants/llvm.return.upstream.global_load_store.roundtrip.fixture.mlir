"builtin.module"() ({
  "llvm.mlir.global"() <{addr_space = 0 : i32, alignment = 4 : i64, global_type = i32, linkage = #llvm.linkage<external>, sym_name = "g", tls_mode = 0 : i64, unnamed_addr = 0 : i64, value = 41 : i32, visibility_ = 0 : i64}> ({
  }) : () -> ()
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<i32 ()>, linkage = #llvm.linkage<external>, sym_name = "main", visibility_ = 0 : i64}> ({
    %0 = "llvm.mlir.constant"() <{value = 1 : i32}> : () -> i32
    %1 = "llvm.mlir.addressof"() <{global_name = @g}> : () -> !llvm.ptr
    %2 = "llvm.load"(%1) <{ordering = 0 : i64}> : (!llvm.ptr) -> i32
    %3 = "llvm.add"(%2, %0) <{overflowFlags = 0 : i32}> : (i32, i32) -> i32
    "llvm.store"(%3, %1) <{ordering = 0 : i64}> : (i32, !llvm.ptr) -> ()
    "llvm.return"(%3) : (i32) -> ()
  }) : () -> ()
}) : () -> ()

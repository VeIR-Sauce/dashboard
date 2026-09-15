"builtin.module"() ({
  "llvm.mlir.global"() <{addr_space = 0 : i32, constant, global_type = !llvm.array<4 x i8>, linkage = #llvm.linkage<private>, sym_name = ".str.1", tls_mode = 0 : i64, value = dense<[104, 105, 33, 0]> : tensor<4xi8>, visibility_ = 0 : i64}> ({
  }) : () -> ()
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<i32 ()>, linkage = #llvm.linkage<external>, sym_name = "\01_lstat", visibility_ = 0 : i64}> ({
    %2 = "llvm.mlir.constant"() <{value = 0 : i32}> : () -> i32
    "llvm.return"(%2) : (i32) -> ()
  }) : () -> ()
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<ptr ()>, linkage = #llvm.linkage<external>, sym_name = "greeting", visibility_ = 0 : i64}> ({
    %0 = "llvm.mlir.addressof"() <{global_name = @".str.1"}> : () -> !llvm.ptr
    %1 = "llvm.mlir.addressof"() <{global_name = @"\01_lstat"}> : () -> !llvm.ptr
    "llvm.return"(%0) : (!llvm.ptr) -> ()
  }) : () -> ()
}) : () -> ()

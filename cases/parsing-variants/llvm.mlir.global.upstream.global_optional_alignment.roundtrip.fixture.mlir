"builtin.module"() ({
  "llvm.mlir.global"() <{addr_space = 0 : i32, global_type = i32, linkage = #llvm.linkage<external>, sym_name = "no_align", tls_mode = 0 : i64, value = 41 : i32, visibility_ = 0 : i64}> ({
  }) : () -> ()
  "llvm.mlir.global"() <{addr_space = 0 : i32, alignment = 4 : i64, global_type = i32, linkage = #llvm.linkage<external>, sym_name = "with_align", tls_mode = 0 : i64, value = 42 : i32, visibility_ = 0 : i64}> ({
  }) : () -> ()
}) : () -> ()

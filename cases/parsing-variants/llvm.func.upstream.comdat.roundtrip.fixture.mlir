"builtin.module"() ({
  "llvm.comdat"() <{sym_name = "c"}> ({
    "llvm.comdat_selector"() <{comdat = 0 : i64, sym_name = "any"}> : () -> ()
    "llvm.comdat_selector"() <{comdat = 1 : i64, sym_name = "exactmatch"}> : () -> ()
    "llvm.comdat_selector"() <{comdat = 2 : i64, sym_name = "largest"}> : () -> ()
    "llvm.comdat_selector"() <{comdat = 3 : i64, sym_name = "nodeduplicate"}> : () -> ()
    "llvm.comdat_selector"() <{comdat = 4 : i64, sym_name = "samesize"}> : () -> ()
  }) : () -> ()
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, comdat = @c::@any, function_type = !llvm.func<void ()>, linkage = #llvm.linkage<external>, sym_name = "f", visibility_ = 0 : i64}> ({
  }) : () -> ()
  "llvm.mlir.global"() <{addr_space = 0 : i32, comdat = @c::@largest, global_type = i32, linkage = #llvm.linkage<external>, sym_name = "g", tls_mode = 0 : i64, value = 0 : i32, visibility_ = 0 : i64}> ({
  }) : () -> ()
}) : () -> ()

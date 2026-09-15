"builtin.module"() ({
  "llvm.comdat"() <{sym_name = "__llvm_comdat"}> ({
    "llvm.comdat_selector"() <{comdat = 0 : i64, sym_name = "any_comdat"}> : () -> ()
    "llvm.comdat_selector"() <{comdat = 1 : i64, sym_name = "exactmatch_comdat"}> : () -> ()
    "llvm.comdat_selector"() <{comdat = 2 : i64, sym_name = "largest_comdat"}> : () -> ()
    "llvm.comdat_selector"() <{comdat = 3 : i64, sym_name = "nodeduplicate_comdat"}> : () -> ()
    "llvm.comdat_selector"() <{comdat = 4 : i64, sym_name = "samesize_comdat"}> : () -> ()
  }) : () -> ()
}) : () -> ()

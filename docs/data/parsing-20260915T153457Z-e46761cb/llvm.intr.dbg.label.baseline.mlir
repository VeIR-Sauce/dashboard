"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void ()>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
    "llvm.intr.dbg.label"() <{label = #llvm.di_label<scope = #llvm.di_lexical_block<scope = #llvm.di_subprogram<scope = #llvm.di_composite_type<tag = DW_TAG_class_type, name = "class_name", file = <"debuginfo.mlir" in "/test/">, scope = #llvm.di_namespace<name = "nested", scope = #llvm.di_namespace<name = "toplevel", exportSymbols = true>, exportSymbols = false>, flags = "TypePassByReference|NonTrivial">, file = <"debuginfo.mlir" in "/test/">, type = <types = #llvm.di_basic_type<tag = DW_TAG_base_type, name = "int1", sizeInBits = 32, encoding = DW_ATE_signed>, #llvm.di_basic_type<tag = DW_TAG_base_type, name = "int1", sizeInBits = 32, encoding = DW_ATE_signed>>>>, name = "label", file = <"debuginfo.mlir" in "/test/">, line = 42>}> : () -> ()
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

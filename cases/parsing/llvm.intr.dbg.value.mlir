"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (i32)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: i32):
    "llvm.intr.dbg.value"(%arg0) <{locationExpr = #llvm.di_expression<[DW_OP_LLVM_fragment(16, 8), DW_OP_plus_uconst(2), DW_OP_deref]>, varInfo = #llvm.di_local_variable<scope = #llvm.di_lexical_block<scope = #llvm.di_subprogram<scope = #llvm.di_composite_type<tag = DW_TAG_class_type, name = "class_name", file = <"debuginfo.mlir" in "/test/">, scope = #llvm.di_namespace<name = "nested", scope = #llvm.di_namespace<name = "toplevel", exportSymbols = true>, exportSymbols = false>, flags = "TypePassByReference|NonTrivial">, file = <"debuginfo.mlir" in "/test/">, type = <types = #llvm.di_basic_type<tag = DW_TAG_base_type, name = "int1", sizeInBits = 32, encoding = DW_ATE_signed>, #llvm.di_basic_type<tag = DW_TAG_base_type, name = "int1", sizeInBits = 32, encoding = DW_ATE_signed>>>>, name = "arg1">}> : (i32) -> ()
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

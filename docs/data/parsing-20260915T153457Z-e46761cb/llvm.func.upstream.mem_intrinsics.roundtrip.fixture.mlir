"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (ptr, ptr, i8, i64)>, linkage = #llvm.linkage<external>, sym_name = "copies", visibility_ = 0 : i64}> ({
  ^bb0(%arg0: !llvm.ptr, %arg1: !llvm.ptr, %arg2: i8, %arg3: i64):
    "llvm.intr.memset"(%arg0, %arg2, %arg3) <{arg_attrs = [{llvm.align = 8 : i64, llvm.nonnull, llvm.noundef}, {}, {}], isVolatile = false}> : (!llvm.ptr, i8, i64) -> ()
    "llvm.intr.memcpy"(%arg0, %arg1, %arg3) <{isVolatile = true}> : (!llvm.ptr, !llvm.ptr, i64) -> ()
    "llvm.intr.memmove"(%arg0, %arg1, %arg3) <{isVolatile = false}> : (!llvm.ptr, !llvm.ptr, i64) -> ()
    "llvm.intr.memcpy"(%arg0, %arg1, %arg3) <{access_groups = [], alias_scopes = [], isVolatile = false, noalias_scopes = [], tbaa = [#llvm.tbaa_tag<base_type = <id = "int", members = {<#llvm.tbaa_root<id = "Simple C/C++ TBAA">, 0>}>, access_type = <id = "int", members = {<#llvm.tbaa_root<id = "Simple C/C++ TBAA">, 0>}>, offset = 0>]}> : (!llvm.ptr, !llvm.ptr, i64) -> ()
    "llvm.intr.memset"(%arg0, %arg2, %arg3) <{isVolatile = false, res_attrs = []}> : (!llvm.ptr, i8, i64) -> ()
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

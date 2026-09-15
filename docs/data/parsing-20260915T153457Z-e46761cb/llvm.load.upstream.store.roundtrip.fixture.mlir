"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<i64 (i64)>, linkage = #llvm.linkage<external>, sym_name = "store_load", visibility_ = 0 : i64}> ({
  ^bb0(%arg0: i64):
    %0 = "llvm.mlir.constant"() <{value = 1 : i64}> : () -> i64
    %1 = "llvm.alloca"(%0) <{alignment = 0 : i64, elem_type = i64}> : (i64) -> !llvm.ptr
    "llvm.store"(%arg0, %1) <{access_groups = [], alias_scopes = [], alignment = 0 : i64, noalias_scopes = [], ordering = 0 : i64, tbaa = []}> : (i64, !llvm.ptr) -> ()
    %2 = "llvm.load"(%1) <{access_groups = [], alias_scopes = [], alignment = 0 : i64, noalias_scopes = [], ordering = 0 : i64, tbaa = []}> : (!llvm.ptr) -> i64
    "llvm.return"(%2) : (i64) -> ()
  }) : () -> ()
}) : () -> ()

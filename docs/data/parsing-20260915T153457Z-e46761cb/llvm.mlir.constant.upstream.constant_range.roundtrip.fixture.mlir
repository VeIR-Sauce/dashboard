"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, arg_attrs = [{llvm.noundef, llvm.range = #llvm.constant_range<i32, 0, 20>}], function_type = !llvm.func<i32 (i32)>, linkage = #llvm.linkage<external>, res_attrs = [{llvm.noundef, llvm.range = #llvm.constant_range<i32, 0, 19>}], sym_name = "callee", visibility_ = 0 : i64}> ({
  ^bb0(%arg0: i32):
    "llvm.return"(%arg0) : (i32) -> ()
  }) : () -> ()
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<i64 ()>, linkage = #llvm.linkage<external>, res_attrs = [{llvm.range = #llvm.constant_range<i32, 0, -7>}], sym_name = "wrapping", visibility_ = 0 : i64}> ({
    %0 = "llvm.mlir.constant"() <{value = 0 : i64}> : () -> i64
    "llvm.return"(%0) : (i64) -> ()
  }) : () -> ()
}) : () -> ()

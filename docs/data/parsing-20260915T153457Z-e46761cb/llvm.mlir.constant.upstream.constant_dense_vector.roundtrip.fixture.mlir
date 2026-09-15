"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void ()>, linkage = #llvm.linkage<external>, sym_name = "splats", visibility_ = 0 : i64}> ({
    %0 = "llvm.mlir.constant"() <{value = dense<1> : vector<2xi32>}> : () -> vector<2xi32>
    %1 = "llvm.mlir.constant"() <{value = dense<[1, 2, 3, 4]> : vector<4xi16>}> : () -> vector<4xi16>
    %2 = "llvm.mlir.constant"() <{value = dense<[104, 105]> : tensor<2xi8>}> : () -> !llvm.array<2 x i8>
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

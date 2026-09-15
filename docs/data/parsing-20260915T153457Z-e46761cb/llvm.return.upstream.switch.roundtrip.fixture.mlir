"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<i32 (i32)>, linkage = #llvm.linkage<external>, sym_name = "no_cases", visibility_ = 0 : i64}> ({
  ^bb0(%arg2: i32):
    "llvm.switch"(%arg2)[^bb1] <{case_operand_segments = array<i32>, operandSegmentSizes = array<i32: 1, 0, 0>}> : (i32) -> ()
  ^bb1:  // pred: ^bb0
    "llvm.return"(%arg2) : (i32) -> ()
  }) : () -> ()
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<i32 (i32)>, linkage = #llvm.linkage<external>, sym_name = "weighted", visibility_ = 0 : i64}> ({
  ^bb0(%arg1: i32):
    "llvm.switch"(%arg1)[^bb1, ^bb2, ^bb3] <{branch_weights = array<i32: 1, 2, 3>, case_operand_segments = array<i32: 0, 0>, case_values = dense<[13, 35]> : vector<2xi32>, operandSegmentSizes = array<i32: 1, 0, 0>}> : (i32) -> ()
  ^bb1:  // pred: ^bb0
    "llvm.return"(%arg1) : (i32) -> ()
  ^bb2:  // pred: ^bb0
    "llvm.return"(%arg1) : (i32) -> ()
  ^bb3:  // pred: ^bb0
    "llvm.return"(%arg1) : (i32) -> ()
  }) : () -> ()
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<i32 (i32)>, linkage = #llvm.linkage<external>, sym_name = "forwarding", visibility_ = 0 : i64}> ({
  ^bb0(%arg0: i32):
    %0 = "llvm.mlir.constant"() <{value = 7 : i32}> : () -> i32
    "llvm.switch"(%arg0, %0, %arg0, %0, %0, %arg0)[^bb1, ^bb2, ^bb2] <{case_operand_segments = array<i32: 2, 2>, case_values = dense<[5, 0]> : vector<2xi32>, operandSegmentSizes = array<i32: 1, 1, 4>}> : (i32, i32, i32, i32, i32, i32) -> ()
  ^bb1(%1: i32):  // pred: ^bb0
    "llvm.return"(%1) : (i32) -> ()
  ^bb2(%2: i32, %3: i32):  // 2 preds: ^bb0, ^bb0
    "llvm.return"(%2) : (i32) -> ()
  }) : () -> ()
}) : () -> ()

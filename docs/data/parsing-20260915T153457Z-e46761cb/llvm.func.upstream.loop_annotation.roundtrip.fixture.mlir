"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (i1)>, linkage = #llvm.linkage<external>, sym_name = "loop", visibility_ = 0 : i64}> ({
  ^bb0(%arg0: i1):
    "llvm.cond_br"(%arg0)[^bb1, ^bb3] <{loop_annotation = #llvm.loop_annotation<mustProgress = true>, operandSegmentSizes = array<i32: 1, 0, 0>}> : (i1) -> ()
  ^bb1:  // pred: ^bb0
    "llvm.br"()[^bb2] <{loop_annotation = #llvm.loop_annotation<unroll = <runtimeDisable = true>, mustProgress = true, isVectorized = true>}> : () -> ()
  ^bb2:  // pred: ^bb1
    "llvm.br"()[^bb3] <{loop_annotation = #llvm.loop_annotation<peeled = <count = 2 : i32>, mustProgress = true>}> : () -> ()
  ^bb3:  // 2 preds: ^bb0, ^bb2
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

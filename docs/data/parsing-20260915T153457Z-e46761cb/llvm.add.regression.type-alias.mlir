!word = i64
"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (!word, !word)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : !word, visibility_ = 0 : !word}> ({
  ^bb0(%arg0: !word, %arg1: !word):
    %0 = "llvm.add"(%arg0, %arg1) <{overflowFlags = 0 : i32}> : (!word, !word) -> !word
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

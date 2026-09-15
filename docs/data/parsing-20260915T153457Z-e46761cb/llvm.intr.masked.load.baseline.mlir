"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (ptr, vector<7xi1>)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: !llvm.ptr, %arg1: vector<7xi1>):
    %0 = "llvm.intr.masked.load"(%arg0, %arg1) <{alignment = 1 : i32}> : (!llvm.ptr, vector<7xi1>) -> vector<7xf32>
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

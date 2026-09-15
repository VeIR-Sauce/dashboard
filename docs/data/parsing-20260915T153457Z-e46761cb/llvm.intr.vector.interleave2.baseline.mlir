"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (vector<[4]xf16>, vector<[4]xf16>)>, linkage = #llvm.linkage<external>, sym_name = "sample", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: vector<[4]xf16>, %arg1: vector<[4]xf16>):
    %0 = "llvm.intr.vector.interleave2"(%arg0, %arg1) : (vector<[4]xf16>, vector<[4]xf16>) -> vector<[8]xf16>
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

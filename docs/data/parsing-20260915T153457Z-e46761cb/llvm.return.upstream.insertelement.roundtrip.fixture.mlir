"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<vector<4xi32> (vector<4xi32>, i32, i1, i8, i32, i64, i128)>, linkage = #llvm.linkage<external>, sym_name = "integer_indices", visibility_ = 0 : i64}> ({
  ^bb0(%arg16: vector<4xi32>, %arg17: i32, %arg18: i1, %arg19: i8, %arg20: i32, %arg21: i64, %arg22: i128):
    %11 = "llvm.insertelement"(%arg16, %arg17, %arg18) : (vector<4xi32>, i32, i1) -> vector<4xi32>
    %12 = "llvm.insertelement"(%11, %arg17, %arg19) : (vector<4xi32>, i32, i8) -> vector<4xi32>
    %13 = "llvm.insertelement"(%12, %arg17, %arg20) : (vector<4xi32>, i32, i32) -> vector<4xi32>
    %14 = "llvm.insertelement"(%13, %arg17, %arg21) : (vector<4xi32>, i32, i64) -> vector<4xi32>
    %15 = "llvm.insertelement"(%14, %arg17, %arg22) : (vector<4xi32>, i32, i128) -> vector<4xi32>
    "llvm.return"(%15) : (vector<4xi32>) -> ()
  }) : () -> ()
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<vector<4xi32> (vector<4xi32>, i32)>, linkage = #llvm.linkage<external>, sym_name = "out_of_range", visibility_ = 0 : i64}> ({
  ^bb0(%arg14: vector<4xi32>, %arg15: i32):
    %7 = "llvm.mlir.constant"() <{value = 4 : i32}> : () -> i32
    %8 = "llvm.mlir.constant"() <{value = -1 : i32}> : () -> i32
    %9 = "llvm.insertelement"(%arg14, %arg15, %7) : (vector<4xi32>, i32, i32) -> vector<4xi32>
    %10 = "llvm.insertelement"(%9, %arg15, %8) : (vector<4xi32>, i32, i32) -> vector<4xi32>
    "llvm.return"(%10) : (vector<4xi32>) -> ()
  }) : () -> ()
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<vector<1xi1> (i1, i64)>, linkage = #llvm.linkage<external>, sym_name = "single_lane", visibility_ = 0 : i64}> ({
  ^bb0(%arg12: i1, %arg13: i64):
    %5 = "llvm.mlir.poison"() : () -> vector<1xi1>
    %6 = "llvm.insertelement"(%5, %arg12, %arg13) : (vector<1xi1>, i1, i64) -> vector<1xi1>
    "llvm.return"(%6) : (vector<1xi1>) -> ()
  }) : () -> ()
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<vector<2x!llvm.ptr> (vector<2x!llvm.ptr>, ptr, i64)>, linkage = #llvm.linkage<external>, sym_name = "pointers", visibility_ = 0 : i64}> ({
  ^bb0(%arg9: vector<2x!llvm.ptr>, %arg10: !llvm.ptr, %arg11: i64):
    %4 = "llvm.insertelement"(%arg9, %arg10, %arg11) : (vector<2x!llvm.ptr>, !llvm.ptr, i64) -> vector<2x!llvm.ptr>
    "llvm.return"(%4) : (vector<2x!llvm.ptr>) -> ()
  }) : () -> ()
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (vector<2xbf16>, bf16, vector<4xf16>, f16, vector<2xf32>, f32, vector<2xf64>, f64, i32)>, linkage = #llvm.linkage<external>, sym_name = "floats", visibility_ = 0 : i64}> ({
  ^bb0(%arg0: vector<2xbf16>, %arg1: bf16, %arg2: vector<4xf16>, %arg3: f16, %arg4: vector<2xf32>, %arg5: f32, %arg6: vector<2xf64>, %arg7: f64, %arg8: i32):
    %0 = "llvm.insertelement"(%arg0, %arg1, %arg8) : (vector<2xbf16>, bf16, i32) -> vector<2xbf16>
    %1 = "llvm.insertelement"(%arg2, %arg3, %arg8) : (vector<4xf16>, f16, i32) -> vector<4xf16>
    %2 = "llvm.insertelement"(%arg4, %arg5, %arg8) : (vector<2xf32>, f32, i32) -> vector<2xf32>
    %3 = "llvm.insertelement"(%arg6, %arg7, %arg8) : (vector<2xf64>, f64, i32) -> vector<2xf64>
    "llvm.return"() : () -> ()
  }) : () -> ()
}) : () -> ()

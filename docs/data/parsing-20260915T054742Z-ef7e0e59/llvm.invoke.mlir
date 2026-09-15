"builtin.module"() ({
  "llvm.mlir.global"() <{addr_space = 0 : i32, constant, global_type = !llvm.ptr, linkage = #llvm.linkage<external>, sym_name = "_ZTIi", tls_mode = 0 : i64, unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  }) : () -> ()
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (ptr)>, linkage = #llvm.linkage<external>, sym_name = "foo", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  }) : () -> ()
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (ptr, ...)>, linkage = #llvm.linkage<external>, sym_name = "vararg_foo", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  }) : () -> ()
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<ptr (ptr)>, linkage = #llvm.linkage<external>, sym_name = "bar", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  }) : () -> ()
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<i32 (...)>, linkage = #llvm.linkage<external>, sym_name = "__gxx_personality_v0", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  }) : () -> ()
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<i32 ()>, linkage = #llvm.linkage<external>, personality = @__gxx_personality_v0, sym_name = "invokeLandingpad", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
    %0 = "llvm.mlir.constant"() <{value = 0 : i32}> : () -> i32
    %1 = "llvm.mlir.constant"() <{value = dense<0> : vector<1xi8>}> : () -> !llvm.array<1 x i8>
    %2 = "llvm.mlir.addressof"() <{global_name = @_ZTIi}> : () -> !llvm.ptr
    %3 = "llvm.mlir.zero"() : () -> !llvm.ptr
    %4 = "llvm.mlir.constant"() <{value = 1 : i32}> : () -> i32
    %5 = "llvm.alloca"(%4) <{elem_type = i8}> : (i32) -> !llvm.ptr
    "llvm.invoke"(%5)[^bb2, ^bb1] <{CConv = #llvm.cconv<ccc>, callee = @foo, op_bundle_sizes = array<i32>, operandSegmentSizes = array<i32: 1, 0, 0, 0>}> : (!llvm.ptr) -> ()
  ^bb1:  // 4 preds: ^bb0, ^bb3, ^bb4, ^bb5
    %6 = "llvm.landingpad"(%3, %2, %1) : (!llvm.ptr, !llvm.ptr, !llvm.array<1 x i8>) -> !llvm.struct<(ptr, i32)>
    "llvm.br"()[^bb3] : () -> ()
  ^bb2:  // 4 preds: ^bb0, ^bb3, ^bb4, ^bb5
    "llvm.return"(%4) : (i32) -> ()
  ^bb3:  // pred: ^bb1
    %7 = "llvm.invoke"(%5)[^bb2, ^bb1] <{CConv = #llvm.cconv<ccc>, callee = @bar, op_bundle_sizes = array<i32>, operandSegmentSizes = array<i32: 1, 0, 0, 0>}> : (!llvm.ptr) -> !llvm.ptr
  ^bb4:  // no predecessors
    "llvm.invoke"(%5, %0)[^bb2, ^bb1] <{CConv = #llvm.cconv<ccc>, callee = @vararg_foo, op_bundle_sizes = array<i32>, operandSegmentSizes = array<i32: 2, 0, 0, 0>, var_callee_type = !llvm.func<void (ptr, ...)>}> : (!llvm.ptr, i32) -> ()
  ^bb5:  // no predecessors
    %8 = "llvm.mlir.undef"() : () -> !llvm.ptr
    "llvm.invoke"(%8, %5, %0)[^bb2, ^bb1] <{CConv = #llvm.cconv<ccc>, op_bundle_sizes = array<i32>, operandSegmentSizes = array<i32: 3, 0, 0, 0>, var_callee_type = !llvm.func<void (ptr, ...)>}> : (!llvm.ptr, !llvm.ptr, i32) -> ()
  }) : () -> ()
}) : () -> ()

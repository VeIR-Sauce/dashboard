"builtin.module"() ({
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<struct<(i32, f64, i32)> (i32, ...)>, linkage = #llvm.linkage<external>, sym_name = "vararg_foo", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  }) : () -> ()
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<struct<(i32, f64, i32)> (i32)>, linkage = #llvm.linkage<external>, sym_name = "foo", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  ^bb0(%arg0: i32):
    %15 = "llvm.mlir.constant"() <{value = 3 : i64}> : () -> i32
    %16 = "llvm.mlir.constant"() <{value = 3 : i64}> : () -> i32
    %17 = "llvm.mlir.constant"() <{value = 4.200000e+01 : f64}> : () -> f64
    %18 = "llvm.mlir.constant"() <{value = 4.200000e+01 : f64}> : () -> f64
    %19 = "llvm.add"(%15, %16) <{overflowFlags = 0 : i32}> : (i32, i32) -> i32
    %20 = "llvm.mul"(%19, %16) <{overflowFlags = 0 : i32}> : (i32, i32) -> i32
    %21 = "llvm.fadd"(%17, %18) <{fastmathFlags = #llvm.fastmath<none>}> : (f64, f64) -> f64
    %22 = "llvm.fsub"(%18, %21) <{fastmathFlags = #llvm.fastmath<none>}> : (f64, f64) -> f64
    %23 = "llvm.mlir.constant"() <{value = 1 : i64}> : () -> i1
    "llvm.cond_br"(%23, %19, %19)[^bb1, ^bb2] <{operandSegmentSizes = array<i32: 1, 1, 1>}> : (i1, i32, i32) -> ()
  ^bb1(%24: i32):  // pred: ^bb0
    %25 = "llvm.call"(%24) <{CConv = #llvm.cconv<ccc>, TailCallKind = #llvm.tailcallkind<none>, callee = @foo, fastmathFlags = #llvm.fastmath<none>, op_bundle_sizes = array<i32>, operandSegmentSizes = array<i32: 1, 0>}> : (i32) -> !llvm.struct<(i32, f64, i32)>
    %26 = "llvm.extractvalue"(%25) <{position = array<i64: 0>}> : (!llvm.struct<(i32, f64, i32)>) -> i32
    %27 = "llvm.extractvalue"(%25) <{position = array<i64: 1>}> : (!llvm.struct<(i32, f64, i32)>) -> f64
    %28 = "llvm.extractvalue"(%25) <{position = array<i64: 2>}> : (!llvm.struct<(i32, f64, i32)>) -> i32
    %29 = "llvm.mlir.undef"() : () -> !llvm.struct<(i32, f64, i32)>
    %30 = "llvm.insertvalue"(%29, %20) <{position = array<i64: 0>}> : (!llvm.struct<(i32, f64, i32)>, i32) -> !llvm.struct<(i32, f64, i32)>
    %31 = "llvm.insertvalue"(%30, %22) <{position = array<i64: 1>}> : (!llvm.struct<(i32, f64, i32)>, f64) -> !llvm.struct<(i32, f64, i32)>
    %32 = "llvm.insertvalue"(%31, %26) <{position = array<i64: 2>}> : (!llvm.struct<(i32, f64, i32)>, i32) -> !llvm.struct<(i32, f64, i32)>
    "llvm.return"(%32) : (!llvm.struct<(i32, f64, i32)>) -> ()
  ^bb2(%33: i32):  // pred: ^bb0
    %34 = "llvm.mlir.undef"() : () -> !llvm.struct<(i32, f64, i32)>
    %35 = "llvm.insertvalue"(%34, %33) <{position = array<i64: 0>}> : (!llvm.struct<(i32, f64, i32)>, i32) -> !llvm.struct<(i32, f64, i32)>
    %36 = "llvm.insertvalue"(%35, %22) <{position = array<i64: 1>}> : (!llvm.struct<(i32, f64, i32)>, f64) -> !llvm.struct<(i32, f64, i32)>
    %37 = "llvm.insertvalue"(%36, %20) <{position = array<i64: 2>}> : (!llvm.struct<(i32, f64, i32)>, i32) -> !llvm.struct<(i32, f64, i32)>
    "llvm.return"(%37) : (!llvm.struct<(i32, f64, i32)>) -> ()
  }) : () -> ()
  "llvm.mlir.global"() <{addr_space = 0 : i32, constant, global_type = !llvm.ptr, linkage = #llvm.linkage<external>, sym_name = "_ZTIi", tls_mode = 0 : i64, unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  }) : () -> ()
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<void (ptr, ptr, ptr)>, linkage = #llvm.linkage<external>, sym_name = "bar", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  }) : () -> ()
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<i32 (...)>, linkage = #llvm.linkage<external>, sym_name = "__gxx_personality_v0", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
  }) : () -> ()
  "llvm.func"() <{CConv = #llvm.cconv<ccc>, function_type = !llvm.func<i32 ()>, linkage = #llvm.linkage<external>, personality = @__gxx_personality_v0, sym_name = "invokeLandingpad", unnamed_addr = 0 : i64, visibility_ = 0 : i64}> ({
    %0 = "llvm.mlir.constant"() <{value = 0 : i32}> : () -> i32
    %1 = "llvm.mlir.constant"() <{value = 3 : i32}> : () -> i32
    %2 = "llvm.mlir.constant"() <{value = "\01"}> : () -> !llvm.array<1 x i8>
    %3 = "llvm.mlir.zero"() : () -> !llvm.ptr
    %4 = "llvm.mlir.addressof"() <{global_name = @_ZTIi}> : () -> !llvm.ptr
    %5 = "llvm.mlir.constant"() <{value = 1 : i32}> : () -> i32
    %6 = "llvm.alloca"(%5) <{elem_type = i8}> : (i32) -> !llvm.ptr
    %7 = "llvm.invoke"(%5)[^bb2, ^bb1] <{CConv = #llvm.cconv<ccc>, callee = @foo, op_bundle_sizes = array<i32>, operandSegmentSizes = array<i32: 1, 0, 0, 0>}> : (i32) -> !llvm.struct<(i32, f64, i32)>
  ^bb1:  // 5 preds: ^bb0, ^bb3, ^bb4, ^bb5, ^bb6
    %8 = "llvm.landingpad"(%3, %4, %2) <{cleanup}> : (!llvm.ptr, !llvm.ptr, !llvm.array<1 x i8>) -> !llvm.struct<(ptr, i32)>
    %9 = "llvm.intr.eh.typeid.for"(%4) : (!llvm.ptr) -> i32
    "llvm.resume"(%8) : (!llvm.struct<(ptr, i32)>) -> ()
  ^bb2:  // 5 preds: ^bb0, ^bb3, ^bb4, ^bb5, ^bb6
    "llvm.return"(%5) : (i32) -> ()
  ^bb3:  // no predecessors
    "llvm.invoke"(%6, %4, %3)[^bb2, ^bb1] <{CConv = #llvm.cconv<ccc>, callee = @bar, op_bundle_sizes = array<i32>, operandSegmentSizes = array<i32: 3, 0, 0, 0>}> : (!llvm.ptr, !llvm.ptr, !llvm.ptr) -> ()
  ^bb4:  // no predecessors
    %10 = "llvm.mlir.addressof"() <{global_name = @foo}> : () -> !llvm.ptr
    %11 = "llvm.invoke"(%10, %5)[^bb2, ^bb1] <{CConv = #llvm.cconv<ccc>, op_bundle_sizes = array<i32>, operandSegmentSizes = array<i32: 2, 0, 0, 0>}> : (!llvm.ptr, i32) -> !llvm.struct<(i32, f64, i32)>
  ^bb5:  // no predecessors
    %12 = "llvm.invoke"(%5, %5)[^bb2, ^bb1] <{CConv = #llvm.cconv<ccc>, callee = @vararg_foo, op_bundle_sizes = array<i32>, operandSegmentSizes = array<i32: 2, 0, 0, 0>, var_callee_type = !llvm.func<struct<(i32, f64, i32)> (i32, ...)>}> : (i32, i32) -> !llvm.struct<(i32, f64, i32)>
  ^bb6:  // no predecessors
    %13 = "llvm.mlir.addressof"() <{global_name = @vararg_foo}> : () -> !llvm.ptr
    %14 = "llvm.invoke"(%13, %5, %5)[^bb2, ^bb1] <{CConv = #llvm.cconv<ccc>, op_bundle_sizes = array<i32>, operandSegmentSizes = array<i32: 3, 0, 0, 0>, var_callee_type = !llvm.func<struct<(i32, f64, i32)> (i32, ...)>}> : (!llvm.ptr, i32, i32) -> !llvm.struct<(i32, f64, i32)>
  ^bb7:  // no predecessors
    "llvm.return"(%0) : (i32) -> ()
  }) : () -> ()
}) : () -> ()

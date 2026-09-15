#!/usr/bin/env python3
"""
Convert standard MLIR test files (with llvm.func, pretty-printed format)
into veir-compatible .mlir files (generic format, no llvm.func, func.return).

Reads argument values from an // ARGS: comment in the input file, or uses defaults.

Usage:
    python3 convert.py input.mlir              # uses ARGS comment or defaults
    python3 convert.py input.mlir --args=7,3   # override arg values
    python3 convert.py input.mlir -o out.mlir  # write to file

Pipeline:
    1. mlir-opt --mlir-print-op-generic  →  generic format
    2. Extract function body from llvm.func
    3. Replace block args with llvm.constant ops
    4. Convert overflowFlags/exact int attrs to unit attrs (nsw, nuw, exact, disjoint)
    5. Replace llvm.return → func.return
    6. Wrap in builtin.module
"""

import sys
import re
import subprocess
import shutil
import os
import argparse


# Default argument values — small, non-zero, co-prime
DEFAULT_ARG_VALUES = [7, 3, 5, 11, 2, 13, 17, 19]


def find_mlir_opt() -> str:
    path = os.environ.get("MLIR_OPT") or shutil.which("mlir-opt")
    if not path:
        print(
            "Error: mlir-opt not found. Set MLIR_OPT env var or add it to PATH.",
            file=sys.stderr,
        )
        sys.exit(1)
    return path


def read_args_from_file(input_path):
    """Read // ARGS: comment from the input MLIR file."""
    with open(input_path) as f:
        for line in f:
            m = re.match(r"\s*//\s*ARGS:\s*(.+)", line)
            if m:
                return [int(x.strip()) for x in m.group(1).split(",")]
    return None


def run_mlir_opt(mlir_opt: str, input_path: str) -> str:
    result = subprocess.run(
        [mlir_opt, "--mlir-print-op-generic", input_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"mlir-opt failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout


def convert_overflow_flags(props_str: str) -> str:
    """Convert overflowFlags = N : i32 to nsw/nuw unit attributes."""
    m = re.search(r"overflowFlags\s*=\s*(\d+)\s*:\s*i32", props_str)
    if not m:
        return props_str
    val = int(m.group(1))
    flags = []
    if val & 1:
        flags.append("nsw")
    if val & 2:
        flags.append("nuw")
    if not flags:
        return re.sub(r",?\s*overflowFlags\s*=\s*\d+\s*:\s*i32\s*,?", "", props_str)
    replacement = ", ".join(flags)
    return re.sub(r"overflowFlags\s*=\s*\d+\s*:\s*i32", replacement, props_str)


def convert_exact_flag(props_str: str) -> str:
    """Convert isExact (unit attr or = true/false) to exact."""
    props_str = re.sub(r"isExact\s*=\s*true", "exact", props_str)
    props_str = re.sub(r",?\s*isExact\s*=\s*false\s*,?", "", props_str)
    props_str = re.sub(r"\bisExact\b", "exact", props_str)
    return props_str


def convert_disjoint_flag(props_str: str) -> str:
    """Convert isDisjoint (unit attr or = true/false) to disjoint."""
    props_str = re.sub(r"isDisjoint\s*=\s*true", "disjoint", props_str)
    props_str = re.sub(r",?\s*isDisjoint\s*=\s*false\s*,?", "", props_str)
    props_str = re.sub(r"\bisDisjoint\b", "disjoint", props_str)
    return props_str


def clean_empty_props(line: str) -> str:
    """Remove empty property blocks <{}> or blocks with only whitespace/commas."""
    line = re.sub(r"<\{\s*,?\s*\}>", "", line)
    line = re.sub(r"<\{\s*,\s*\}>", "", line)
    return line


def convert(generic_mlir: str, arg_values: list[int]) -> str:
    lines = generic_mlir.strip().split("\n")

    # Find llvm.func bodies and extract them
    func_bodies = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if '"llvm.func"' in line:
            i += 1
            block_args = []
            body_lines = []
            # Look for ^bb0(...):
            if i < len(lines) and lines[i].strip().startswith("^bb"):
                bb_line = lines[i].strip()
                arg_match = re.findall(r"(%\w+):\s*(i\d+)", bb_line)
                block_args = arg_match
                i += 1

            # Collect body lines until closing }) : () -> ()
            depth = 1
            while i < len(lines):
                cur = lines[i]
                if "({" in cur:
                    depth += 1
                if "})" in cur:
                    depth -= 1
                    if depth == 0:
                        break
                body_lines.append(cur)
                i += 1

            func_bodies.append((block_args, body_lines))
        i += 1

    if not func_bodies:
        print("No llvm.func found in input", file=sys.stderr)
        sys.exit(1)

    # Use the first function
    block_args, body_lines = func_bodies[0]

    # Generate constant definitions for each argument
    const_lines = []
    for idx, (arg_name, arg_type) in enumerate(block_args):
        val = (
            arg_values[idx]
            if idx < len(arg_values)
            else DEFAULT_ARG_VALUES[idx % len(DEFAULT_ARG_VALUES)]
        )
        const_lines.append(
            f'  {arg_name} = "llvm.constant"() <{{ "value" = {val} : {arg_type} }}> : () -> {arg_type}'
        )

    # Process body lines
    processed = []
    for line in body_lines:
        line = convert_overflow_flags(line)
        line = convert_exact_flag(line)
        line = convert_disjoint_flag(line)
        line = line.replace('"llvm.return"', '"func.return"')
        line = line.replace('"llvm.mlir.constant"', '"llvm.constant"')
        line = clean_empty_props(line)
        processed.append(line)

    # Find the last i32-compatible value to return for comparison
    last_val = None
    last_type = None
    for cur in reversed(processed):
        m = re.match(r"\s*(%\w+)\s*=.*->\s*(i\d+)\s*$", cur)
        if m:
            last_val = m.group(1)
            last_type = m.group(2)
            break

    # Replace void "func.return"() with one that returns the last value
    final_processed = []
    for line in processed:
        if '"func.return"()' in line and last_val:
            if last_type == "i32":
                final_processed.append(
                    f'  "func.return"({last_val}) : ({last_type}) -> ()'
                )
            elif last_type and int(last_type[1:]) > 32:
                final_processed.append(
                    f'  %__ret = "llvm.trunc"({last_val}) : ({last_type}) -> i32'
                )
                final_processed.append('  "func.return"(%__ret) : (i32) -> ()')
            elif last_type and int(last_type[1:]) < 32:
                final_processed.append(
                    f'  %__ret = "llvm.zext"({last_val}) : ({last_type}) -> i32'
                )
                final_processed.append('  "func.return"(%__ret) : (i32) -> ()')
            else:
                final_processed.append(line)
        else:
            final_processed.append(line)

    # Build the output
    out_lines = ['"builtin.module"() ({']
    out_lines.extend(const_lines)
    out_lines.extend(final_processed)
    out_lines.append("}) : () -> ()")
    out_lines.append("")

    return "\n".join(out_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Convert LLVM MLIR tests to veir format"
    )
    parser.add_argument("input", help="Input .mlir file")
    parser.add_argument("-o", "--output", help="Output .mlir file (default: stdout)")
    parser.add_argument(
        "--args", help="Comma-separated arg values (e.g., 7,3,5)", default=None
    )
    args = parser.parse_args()

    mlir_opt = find_mlir_opt()

    arg_values = DEFAULT_ARG_VALUES
    if args.args:
        arg_values = [int(x) for x in args.args.split(",")]
    else:
        file_args = read_args_from_file(args.input)
        if file_args:
            arg_values = file_args

    generic = run_mlir_opt(mlir_opt, args.input)
    result = convert(generic, arg_values)

    if args.output:
        with open(args.output, "w") as f:
            f.write(result)
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        print(result)


if __name__ == "__main__":
    main()

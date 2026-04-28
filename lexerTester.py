import os
import sys
import glob
import time
import timeit
from tabulate import tabulate
from patitoLexer import PatitoLexer

"""
Verbose mode time in ms includes I/O operations, not pure lexer performance
"""


# Function to run the lexer on a single file or string
def analyze_file(
    lexer, input_path: str, output_path: str = None
) -> tuple[bool, Exception | None, float]:
    success: bool = False
    error: Exception | None = None

    real_time_start = time.perf_counter()
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = f.read()

        lexer.lexer.lineno = 1
        lexer.input(data)
        tokens = []

        for t in lexer.tokenize():
            tokens.append([t.type, t.value, t.lineno, t.lexpos])

        # If output path is provided, save the detailed token table
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            token_table = tabulate(
                tokens, headers=["Type", "Value", "Line", "GPos"], tablefmt="grid"
            )
            with open(output_path, "w", encoding="utf-8") as f_out:
                f_out.write(token_table)
        success = True

    except Exception as e:
        error = e
        success = False
    finally:
        real_time_end = time.perf_counter()

    elapsed_time = (real_time_end - real_time_start) * 1000
    return success, error, elapsed_time


# Function to run all tests in the 'tests/' directory
def run_all_tests(lexer, verbose: bool = False):
    test_files = sorted(glob.glob("tests/lexer/*.pt"))
    if not test_files:
        print("No tests found in tests/lexer/ directory.")
        return

    print(f"Found {len(test_files)} tests.")

    passed = 0
    failed = 0

    if verbose:
        print("-" * 40)
    for test_file in test_files:
        # Create a corresponding output file for reference
        basename = os.path.basename(test_file)
        name_without_ext = os.path.splitext(basename)[0]
        output_file = f"tests-results/lexer/{name_without_ext}.log"

        success, error, elapsed_time = analyze_file(lexer, test_file, output_file)

        if success:
            passed += 1
        else:
            failed += 1

        if verbose:
            print(f"{'Testing ' + name_without_ext:<25}", end=" ")
            print(f"{elapsed_time:>5.2f} ms", end=" ")
            if success:
                print(f"{'✓ PASS':<10}")
            else:
                print(f"{'✗ FAIL':<10} {error}")

    if verbose:
        print("-" * 40)

    print(f"Test Summary: {passed} Passed, {failed} Failed")


def heavy_test(lexer):
    test_file = "tests/lexer/heavy.pt"
    if not os.path.exists(test_file):
        print(f"Error: Heavy test file '{test_file}' not found.")
        return

    print("Wait...")
    time = timeit.timeit(
        lambda: analyze_file(lexer, test_file, "tests-results/lexer/heavy.log"),
        number=10_000,
    )
    print(f"Heavy test took {time:.2f} seconds.")


if __name__ == "__main__":
    lexer = PatitoLexer()

    run_heavy = False
    is_built = False
    verbose = False

    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg in ["--optimize", "-o"]:
                lexer.build(optimize=1)
                is_built = True
            elif arg in ["--heavy", "-h"]:
                run_heavy = True
            elif arg in ["--verbose", "-v"]:
                verbose = True
            else:
                print(f"Invalid argument: {arg}")

    if not is_built:
        lexer.build()

    run_all_tests(lexer, verbose=verbose)

    if run_heavy:
        heavy_test(lexer)

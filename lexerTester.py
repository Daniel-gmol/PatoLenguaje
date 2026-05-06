import os
import sys
import glob
import time
import timeit
import json
from tabulate import tabulate
from patitoLexer import PatitoLexer

"""
El tiempo medido en modo verbose, incluye operaciones I/O, no el performance puro del lexer
"""


def analyze_file(
    lexer, input_path: str, output_path: str = None
) -> tuple[bool, Exception | None, float, list[dict], list[str]]:
    success: bool = False
    error: Exception | None = None
    tokens_out: list[dict] = []

    real_time_start = time.perf_counter()
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = f.read()

        lexer.lexer.lineno = 1
        lexer.errors = []
        lexer.input(data)
        tokens = []

        for t in lexer.tokenize():
            tokens.append([t.type, t.value, t.lineno, t.lexpos])
            tokens_out.append({"type": t.type, "value": t.value})

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
    return success, error, elapsed_time, tokens_out, lexer.errors


def run_all_tests(lexer, verbose: bool = False):
    test_files = sorted(glob.glob("tests/lexer/*.pt"))
    if not test_files:
        print("No tests found in tests/lexer/ directory.")
        return

    print(f"Found {len(test_files)} tests.")

    passed = 0
    failed = 0

    if verbose:
        print("-" * 50)
    for test_file in test_files:
        basename = os.path.basename(test_file)
        name_without_ext = os.path.splitext(basename)[0]
        output_file = f"tests-results/lexer/{name_without_ext}.log"
        expected_file = f"tests/lexer/{name_without_ext}.expected.json"

        success, error, elapsed_time, tokens, lexer_errors = analyze_file(
            lexer, test_file, output_file
        )

        is_error_test = basename.startswith("error_")
        test_passed = False
        fail_reason = ""

        if not success:
            test_passed = False
            fail_reason = f"Exception: {error}"
        elif is_error_test:
            if len(lexer_errors) > 0:
                test_passed = True
            else:
                test_passed = False
                fail_reason = "Expected lexer errors, but found none."
        else:
            if len(lexer_errors) > 0:
                test_passed = False
                fail_reason = f"Unexpected lexer errors: {lexer_errors}"
            else:
                if not os.path.exists(expected_file):
                    print("No hay archivo esperado, no se puede corroborar")
                else:
                    with open(expected_file, "r", encoding="utf-8") as f:
                        expected_tokens = json.load(f)
                    if tokens == expected_tokens:
                        test_passed = True
                    else:
                        test_passed = False
                        fail_reason = "Tokens do not match expected output."

        if test_passed:
            passed += 1
        else:
            failed += 1

        if verbose:
            print(f"{'Testing ' + name_without_ext:<30}", end=" ")
            print(f"{elapsed_time:>5.2f} ms", end=" ")
            if test_passed:
                msg = f"{'✓ PASS':<10}"
                if "Generated" in fail_reason:
                    msg += " " + fail_reason
                print(msg)
            else:
                print(f"{'✗ FAIL':<10} {fail_reason}")

    if verbose:
        print("-" * 50)

    print(f"Test Summary: {passed} Passed, {failed} Failed")


def heavy_test(lexer):
    test_file = "tests/lexer/heavy.pt"
    if not os.path.exists(test_file):
        print(f"Error: Heavy test file '{test_file}' not found.")
        return

    print("Wait...")
    time_t = timeit.timeit(
        lambda: analyze_file(lexer, test_file, "tests-results/lexer/heavy.log"),
        number=10_000,
    )
    print(f"Heavy test took {time_t:.2f} seconds.")


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

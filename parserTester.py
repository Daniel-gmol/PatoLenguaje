import os
import sys
import glob
import time
from patitoParser import PatitoParser

def analyze_file(
    parser, input_path: str, output_path: str = None
) -> tuple[bool, Exception | None, float, list[str], any, dict | None]:
    success: bool = False
    error: Exception | None = None
    ast = None
    dir_fun = None
    
    real_time_start = time.perf_counter()
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = f.read()

        ast = parser.parse(data)
        dir_fun = parser.dir_fun

        if output_path and ast is not None:
            import pprint
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f_out:
                f_out.write("AST:\n")
                pprint.pprint(ast, stream=f_out)

                f_out.write("\n\nDIR_FUN:\n")
                pprint.pprint(dir_fun, stream=f_out)
        success = True
    except Exception as e:
        error = e
        success = False
    finally:
        real_time_end = time.perf_counter()

    elapsed_time = (real_time_end - real_time_start) * 1000
    
    return success, error, elapsed_time, parser.errors, ast, dir_fun

def run_all_tests(parser, verbose: bool = False):
    test_files = sorted(glob.glob("tests/parser/*.pt"))
    if not test_files:
        print("No tests found in tests/parser/ directory.")
        return

    print(f"Found {len(test_files)} tests.")

    passed = 0
    failed = 0

    if verbose:
        print("-" * 50)
    for test_file in test_files:
        basename = os.path.basename(test_file)
        name_without_ext = os.path.splitext(basename)[0]
        is_error_test = basename.startswith("error_")
        output_file = None if is_error_test else f"tests-results/parser/{name_without_ext}.log"

        success, error, elapsed_time, parser_errors, ast, dir_fun = analyze_file(
            parser, test_file, output_file
        )

        test_passed = False
        fail_reason = ""

        if not success:
            test_passed = False
            fail_reason = f"Exception: {error}"
        elif is_error_test:
            if len(parser_errors) > 0:
                test_passed = True
            else:
                test_passed = False
                fail_reason = "Expected parser errors, but found none."
        else:
            if len(parser_errors) > 0:
                test_passed = False
                fail_reason = f"Unexpected parser errors: {parser_errors[0]}"
            else:
                test_passed = True

        if test_passed:
            passed += 1
        else:
            failed += 1

        if verbose:
            print(f"{'Testing ' + name_without_ext:<30}", end=" ")
            print(f"{elapsed_time:>5.2f} ms", end=" ")
            if test_passed:
                print(f"{'✓ PASS':<10}")
            else:
                print(f"{'✗ FAIL':<10} {fail_reason}")

    if verbose:
        print("-" * 50)

    print(f"Test Summary: {passed} Passed, {failed} Failed")


if __name__ == "__main__":
    parser = PatitoParser()
    
    is_built = False
    verbose = False

    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg in ["--optimize", "-o"]:
                parser.build(optimize=1)
                is_built = True
            elif arg in ["--verbose", "-v"]:
                verbose = True
            else:
                pass

    if not is_built:
        parser.build()

    run_all_tests(parser, verbose=verbose)

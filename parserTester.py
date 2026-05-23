import os
import time
from patitoParser import PatitoParser
from testRunner import TestResult, run_all_tests, create_arg_parser

TEST_DIR = "tests/parser"
RESULTS_DIR = "tests-results/parser"


def analyze_file(parser, input_path: str) -> tuple[bool, list[str]]:
    with open(input_path, "r", encoding="utf-8") as f:
        data = f.read()

    ok = parser.parse(data)
    return ok, list(parser.errors)


def write_parse_log(ok: bool, errors: list[str], output_path: str) -> None:
    if not output_path:
        return
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f_out:
        f_out.write(f"Parse OK: {ok}\n")
        if errors:
            f_out.write("\nErrors:\n")
            for err in errors:
                f_out.write(f"  {err}\n")


def evaluate_test_logic(basename: str, ok: bool, parser_errors: list[str]) -> tuple[bool, str]:
    is_error_test = basename.startswith("error_")

    if is_error_test:
        if not ok or len(parser_errors) > 0:
            return True, ""
        return False, "Esperaba errores en el parser, no se encontraron."

    if not ok or len(parser_errors) > 0:
        return False, f"Error inesperado en el parser: {parser_errors}"

    return True, ""


def run_single_test(parser, test_file: str) -> TestResult:
    basename = os.path.basename(test_file)
    name_without_ext = os.path.splitext(basename)[0]
    output_file = f"{RESULTS_DIR}/{name_without_ext}.log"

    start_time = time.perf_counter()
    try:
        ok, parser_errors = analyze_file(parser, test_file)
        passed, fail_reason = evaluate_test_logic(basename, ok, parser_errors)
        write_parse_log(ok, parser_errors, output_file)
    except Exception as e:
        passed = False
        fail_reason = f"Excepción: {str(e)}"
    finally:
        elapsed_time = (time.perf_counter() - start_time) * 1000

    return TestResult(name_without_ext, passed, elapsed_time, fail_reason)


def main():
    args = create_arg_parser("PatitoParser Test Runner").parse_args()

    parser = PatitoParser()
    parser.build(optimize=1 if args.optimize else 0)

    run_all_tests(TEST_DIR, lambda tf: run_single_test(parser, tf), verbose=args.verbose)


if __name__ == "__main__":
    main()

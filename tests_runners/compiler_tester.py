import os
import pprint
import time
from patito.compiler import PatitoCompiler
from .test_runner import TestResult, run_all_tests, create_arg_parser

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEST_DIR = os.path.join(ROOT_DIR, "tests", "semantic")
RESULTS_DIR = os.path.join(ROOT_DIR, "tests-results", "semantic")


def analyze_file(compiler, input_path: str) -> tuple[bool, list[str], dict | None, list]:
    with open(input_path, "r", encoding="utf-8") as f:
        data = f.read()

    ok = compiler.parse(data)
    errors = list(compiler.errors)
    dir_fun = compiler.dir_fun
    quads = list(compiler.pretty_quads())

    return ok, errors, dir_fun, quads


def write_compile_log(ok: bool, errors: list[str], dir_fun: dict | None, quads: list, output_path: str) -> None:
    if not output_path:
        return
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f_out:
        f_out.write(f"Compile OK: {ok}\n")

        if errors:
            f_out.write("\nErrors:\n")
            for err in errors:
                f_out.write(f"  {err}\n")

        if dir_fun:
            f_out.write("\nDIR_FUN:\n")
            pprint.pprint(dir_fun, stream=f_out)

        if quads:
            f_out.write("\nQuadruples:\n")
            for i, q in enumerate(quads):
                f_out.write(f"  {i:>3}: {q}\n")


def evaluate_test_logic(
    basename: str,
    ok: bool,
    compiler_errors: list[str],
) -> tuple[bool, str]:
    is_error_test = basename.startswith("error_")

    if is_error_test:
        if not ok or len(compiler_errors) > 0:
            return True, ""
        return False, "Esperaba errores semánticos, no se encontraron."

    if not ok or len(compiler_errors) > 0:
        return False, f"Error inesperado en el compilador: {compiler_errors}"

    return True, ""


def run_single_test(compiler, test_file: str) -> TestResult:
    basename = os.path.basename(test_file)
    name_without_ext = os.path.splitext(basename)[0]
    output_file = os.path.join(RESULTS_DIR, f"{name_without_ext}.log")

    start_time = time.perf_counter()
    try:
        ok, compiler_errors, dir_fun, quads = analyze_file(compiler, test_file)
        passed, fail_reason = evaluate_test_logic(basename, ok, compiler_errors)
        write_compile_log(ok, compiler_errors, dir_fun, quads, output_file)
    except Exception as e:
        passed = False
        fail_reason = f"Excepción: {str(e)}"
    finally:
        elapsed_time = (time.perf_counter() - start_time) * 1000

    return TestResult(name_without_ext, passed, elapsed_time, fail_reason)


def main():
    args = create_arg_parser("PatitoCompiler Test Runner").parse_args()

    compiler = PatitoCompiler()
    compiler.build(optimize=1 if args.optimize else 0)

    run_all_tests(TEST_DIR, lambda tf: run_single_test(compiler, tf), verbose=args.verbose)


if __name__ == "__main__":
    main()

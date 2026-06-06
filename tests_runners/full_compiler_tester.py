import os
import sys
import io
import pprint
import time
from patito.compiler import PatitoCompiler
from patito.vm import VirtualMachine
from .test_runner import TestResult, run_all_tests, create_arg_parser

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEST_DIR = os.path.join(ROOT_DIR, "tests", "compiler")
RESULTS_DIR = os.path.join(ROOT_DIR, "tests-results", "compiler")

# Default input to feed to programs that use READ/dame
DEFAULT_INPUT = "0\n" * 20


def compile_file(compiler, input_path: str) -> tuple[bool, list[str], dict | None, list]:
    with open(input_path, "r", encoding="utf-8") as f:
        data = f.read()

    ok = compiler.parse(data)
    errors = list(compiler.errors)
    dir_fun = compiler.dir_fun
    quads = list(compiler.quads)

    return ok, errors, dir_fun, quads


def run_vm(compiler) -> tuple[bool, str]:
    """Run the VM on a successfully compiled program.
    Redirects stdin to provide default input for READ operations.
    Returns (ok, error_message).
    """
    old_stdin = sys.stdin
    old_stdout = sys.stdout
    try:
        sys.stdin = io.StringIO(DEFAULT_INPUT)
        sys.stdout = io.StringIO()
        vm = VirtualMachine(compiler)
        vm.run(debug=False)
        return True, ""
    except Exception as e:
        return False, str(e)
    finally:
        sys.stdin = old_stdin
        sys.stdout = old_stdout


def write_compiler_log(
    ok: bool,
    errors: list[str],
    dir_fun: dict | None,
    quads: list,
    vm_ok: bool,
    vm_error: str,
    output_path: str,
) -> None:
    if not output_path:
        return
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f_out:
        f_out.write(f"Compile OK: {ok}\n")
        f_out.write(f"VM OK: {vm_ok}\n")

        if errors:
            f_out.write("\nCompiler Errors:\n")
            for err in errors:
                f_out.write(f"  {err}\n")

        if vm_error:
            f_out.write(f"\nVM Error:\n  {vm_error}\n")

        if dir_fun:
            f_out.write("\nDIR_FUN:\n")
            pprint.pprint(dir_fun, stream=f_out)

        if quads:
            f_out.write("\nQuadruples:\n")
            for i, q in enumerate(quads):
                f_out.write(f"  {i:>3}: {q}\n")


def evaluate_test_logic(
    basename: str,
    compile_ok: bool,
    compiler_errors: list[str],
    vm_ok: bool,
    vm_error: str,
) -> tuple[bool, str]:
    is_error_test = basename.startswith("error_")

    if is_error_test:
        # Error tests: expect either compile failure OR vm failure
        if not compile_ok or len(compiler_errors) > 0:
            return True, ""
        if not vm_ok:
            return True, ""
        return False, "Esperaba errores, no se encontraron."

    # Normal tests: expect both compile and VM success
    if not compile_ok or len(compiler_errors) > 0:
        return False, f"Error de compilación: {compiler_errors}"

    if not vm_ok:
        return False, f"Error en VM: {vm_error}"

    return True, ""


def run_single_test(compiler, test_file: str) -> TestResult:
    basename = os.path.basename(test_file)
    name_without_ext = os.path.splitext(basename)[0]
    output_file = os.path.join(RESULTS_DIR, f"{name_without_ext}.log")

    start_time = time.perf_counter()
    vm_ok = False
    vm_error = ""
    try:
        compile_ok, compiler_errors, dir_fun, quads = compile_file(compiler, test_file)

        if compile_ok and len(compiler_errors) == 0:
            vm_ok, vm_error = run_vm(compiler)
        else:
            vm_ok = False
            vm_error = "Skipped (compilation failed)"

        passed, fail_reason = evaluate_test_logic(
            basename, compile_ok, compiler_errors, vm_ok, vm_error
        )
        write_compiler_log(
            compile_ok, compiler_errors, dir_fun, quads, vm_ok, vm_error, output_file
        )
    except Exception as e:
        passed = False
        fail_reason = f"Excepción: {str(e)}"
    finally:
        elapsed_time = (time.perf_counter() - start_time) * 1000

    return TestResult(name_without_ext, passed, elapsed_time, fail_reason)


def main():
    args = create_arg_parser("Patito Compiler+VM Test Runner").parse_args()

    compiler = PatitoCompiler()
    compiler.build(optimize=1 if args.optimize else 0)

    run_all_tests(TEST_DIR, lambda tf: run_single_test(compiler, tf), verbose=args.verbose)


if __name__ == "__main__":
    main()

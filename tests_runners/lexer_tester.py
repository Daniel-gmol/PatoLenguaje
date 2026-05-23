import os
import json
import time
from tabulate import tabulate
from patito.lexer import PatitoLexer
from .test_runner import TestResult, run_all_tests, create_arg_parser

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEST_DIR = os.path.join(ROOT_DIR, "tests", "lexer")
RESULTS_DIR = os.path.join(ROOT_DIR, "tests-results", "lexer")


def analyze_file(lexer, input_path: str) -> tuple[list, list[dict], list[str]]:
    with open(input_path, "r", encoding="utf-8") as f:
        data = f.read()

    # reset del estado del lexer 
    lexer.lexer.lineno = 1
    lexer.errors = []
    lexer.input(data)

    tokens_complete = []
    tokens_json = []

    for t in lexer.tokenize():
        tokens_complete.append([t.type, t.value, t.lineno, t.lexpos])
        tokens_json.append({"type": t.type, "value": t.value})

    return tokens_complete, tokens_json, lexer.errors


def write_token_log(tokens: list, output_path: str) -> None:
    if not output_path:
        return
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    token_table = tabulate(
        tokens, headers=["Type", "Value", "Line", "GPos"], tablefmt="grid"
    )
    with open(output_path, "w", encoding="utf-8") as f_out:
        f_out.write(token_table)


def evaluate_test_logic(basename: str, tokens: list[dict], lexer_errors: list[str], expected_file: str) -> tuple[bool, str]:
    is_error_test = basename.startswith("error_")

    if is_error_test:
        if len(lexer_errors) > 0:
            return True, ""
        return False, "Esperaba errores en el lexer, no se encontraron."
        
    if len(lexer_errors) > 0:
        return False, f"Error inesperado en el lexer: {lexer_errors}"

    if not os.path.exists(expected_file):
        return True, "Correcto (No se encontró archivo .expected.json para hacer la comparación)."

    try:
        with open(expected_file, "r", encoding="utf-8") as f:
            expected_tokens = json.load(f)
        if tokens == expected_tokens:
            return True, ""
        unexpected_tokens = [(tokens[i], expected_tokens[i]) for i in range(min(len(tokens), len(expected_tokens))) if tokens[i] != expected_tokens[i]]
        return False, f"Los tokens no coinciden con los esperados: {unexpected_tokens}"
    except json.JSONDecodeError:
        return False, f"Error de formato en el archivo json: {expected_file}"


def run_single_test(lexer, test_file: str) -> TestResult:
    basename = os.path.basename(test_file)
    name_without_ext = os.path.splitext(basename)[0]
    output_file = os.path.join(RESULTS_DIR, f"{name_without_ext}.log")
    expected_file = os.path.join(TEST_DIR, f"{name_without_ext}.expected.json")

    start_time = time.perf_counter()
    try:
        tokens_complete, tokens_json, lexer_errors = analyze_file(lexer, test_file)
        passed, fail_reason = evaluate_test_logic(basename, tokens_json, lexer_errors, expected_file)
        write_token_log(tokens_complete, output_file)
    except Exception as e:
        passed = False
        fail_reason = f"Excepción: {str(e)}"
    finally:
        elapsed_time = (time.perf_counter() - start_time) * 1000

    return TestResult(name_without_ext, passed, elapsed_time, fail_reason)


def main():
    args = create_arg_parser("PatitoLexer Test Runner").parse_args()

    lexer = PatitoLexer()
    lexer.build(optimize=1 if args.optimize else 0)

    run_all_tests(TEST_DIR, lambda tf: run_single_test(lexer, tf), verbose=args.verbose)


if __name__ == "__main__":
    main()
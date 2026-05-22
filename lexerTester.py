import os
import sys
import glob
import time
import timeit
import json
import argparse
from dataclasses import dataclass
from tabulate import tabulate
from patitoLexer import PatitoLexer

@dataclass
class TestResult:
    name: str
    passed: bool
    elapsed_time: float
    fail_reason: str = ""

def analyze_file(lexer, input_path: str) -> tuple[list[dict], list[dict], list[str]]:
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
    output_file = f"tests-results/lexer/{name_without_ext}.log"
    expected_file = f"tests/lexer/{name_without_ext}.expected.json"

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

def run_all_tests(lexer, verbose: bool = False) -> None:
    test_files = sorted(glob.glob("tests/lexer/*.pt"))
    if not test_files:
        print("No se encontraron archivos de prueba en tests/lexer/")
        return

    print(f"Se encontraron {len(test_files)} pruebas.")
    if verbose:
        print("-" * 65)

    results = []
    for tf in test_files:
        result = run_single_test(lexer, tf)
        results.append(result)

        if verbose:
            status = f"{'✓ PASS':<10}" if result.passed else f"{'✗ FAIL':<10}"
            reason = f" {result.fail_reason}" if result.fail_reason else ""
            print(f"Test {result.name:<25} {result.elapsed_time:>6.2f} ms  {status}{reason}")

    if verbose:
        print("-" * 65)

    passed_count = sum(1 for r in results if r.passed)
    failed_count = len(results) - passed_count
    print(f"Resumen: {passed_count} Pasó, {failed_count} Falló")

def main():
    parser = argparse.ArgumentParser(description="PatitoLexer Test Runner")
    parser.add_argument("-o", "--optimize", action="store_true", help="Build lexer with optimizations")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose status printing")
    args = parser.parse_args()

    lexer = PatitoLexer()
    lexer.build(optimize=1 if args.optimize else 0)

    run_all_tests(lexer, verbose=args.verbose)

if __name__ == "__main__":
    main()
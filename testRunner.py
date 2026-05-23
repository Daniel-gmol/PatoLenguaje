import os
import glob
import time
import argparse
from dataclasses import dataclass


SHARED_DIR = "tests/shared"


@dataclass
class TestResult:
    name: str
    passed: bool
    elapsed_time: float
    fail_reason: str = ""


def run_all_tests(suite_dir: str, run_single_test_fn, verbose: bool = False) -> None:
    shared_tests = sorted(glob.glob(f"{SHARED_DIR}/*.pt"))
    suite_tests = sorted(glob.glob(f"{suite_dir}/*.pt"))
    test_files = shared_tests + suite_tests

    if not test_files:
        print(f"No se encontraron archivos de prueba.")
        return

    print(f"Se encontraron {len(test_files)} pruebas.")
    if verbose:
        print("-" * 65)

    results = []
    for tf in test_files:
        result = run_single_test_fn(tf)
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


def create_arg_parser(description: str) -> argparse.ArgumentParser:
    arg_parser = argparse.ArgumentParser(description=description)
    arg_parser.add_argument("-o", "--optimize", action="store_true", help="Build with optimizations")
    arg_parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose status printing")
    return arg_parser

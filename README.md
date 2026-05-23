# Proyecto Patito

Un proyecto sencillito para el lenguaje **Patito**.

![Pingüino](misc/pinguino3334.png)


## Project Structure

```
patito/
├── patito/
│   ├── lexer.py
│   ├── parser.py
│   ├── compiler.py
│   ├── memory.py
│   ├── semantic_cube.py
│
├── tests/
│   ├── shared/
│   ├── lexer/
│   ├── parser/
│   └── semantic/
│
├── tests_runners/
│   ├── test_runner.py
│   ├── lexer_tester.py
│   ├── parser_tester.py
│   └── compiler_tester.py
│
└── requirements.txt
```

---

## Setup and Requirements

The project uses a Python virtual environment. To get started:

```bash
python -m venv .venv
source .venv/bin/activate       # on Unix/macOS
# .venv\Scripts\activate        # on Windows

pip install -r requirements.txt
```

---

## Running the Compiler Directly

Each module in `patito/` has a `main()` entry point and can be invoked individually
from the project root (with the virtual environment active). All three accept an
optional file argument; if omitted, they read from **stdin**.

### Lexer

```bash
python -m patito.lexer <source_file.pt>
# or: echo 'programa foo; fin' | python -m patito.lexer
```

Tokenizes the source file and prints the token stream with any lexical errors.

### Parser

```bash
python -m patito.parser <source_file.pt>
# or: cat program.pt | python -m patito.parser
```

Validates syntax and builds the variable/function directory.

### Compiler (Semantic + IR)

```bash
python -m patito.compiler <source_file.pt>
# or: cat program.pt | python -m patito.compiler
```

Runs full compilation: syntax, semantic checks, and IR generation (quadruples).
Prints the function directory, raw quadruples, and human-readable quadruples.

---

## Running the Test Suites

All test runners live in `tests_runners/` and must be invoked as Python **modules**
from the project root so that relative imports resolve correctly.

### Lexer tests

```bash
python -m tests_runners.lexer_tester
```

### Parser tests

```bash
python -m tests_runners.parser_tester
```

### Compiler / Semantic + IR tests

```bash
python -m tests_runners.compiler_tester
```

Test cases are read from `tests/shared/` (common) and the suite-specific directory.
Each run writes `.log` files to `tests-results/<suite>/`.

---

## Available Options for Test Scripts

All three test runners accept the same flags:

| Flag | Short | Description |
|------|-------|-------------|
| `--verbose` | `-v` | Print per-test timing and pass/fail details |
| `--optimize` | `-o` | Build the lexer/parser with PLY's optimization flag |

**Example – verbose compiler tests with optimization:**

```bash
python -m tests_runners.compiler_tester -v -o
```

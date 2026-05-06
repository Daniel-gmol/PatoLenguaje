# Proyecto Patito

Un proyecto sencillito para el lenguaje Patito.

![Pingüino](misc/pinguino3334.png)


## How to Use the Lexer

The lexer can be run from the command line:

```bash
python lexerTester.py <source_file.pt>
```

It will output tokens and any lexical errors.

## How to Use the Parser

The parser can be executed similarly:

```bash
python parserTester.py <source_file.pt>
```

It will validate the syntax and, if successful, build the AST.

## Running the Test Cases

All lexer and parser test cases are located in the `tests/` directory.

- Lexer tests: `tests/lexer/`
- Parser tests: `tests/parser/`

You can run the full test suite with:

```bash
python lexerTester.py   # runs all lexer tests
python parserTester.py  # runs all parser tests
```

Or run a specific test file by providing its path.

## Available Options for Test Scripts

- **Verbose Mode** (`--verbose` or `-v`)
  - Provides detailed output for each test case, including timing and pass/fail messages.
  - Activate by adding the flag when running the tester, e.g., `python lexerTester.py -v` or `python parserTester.py --verbose`.

- **Optimize Mode** (`--optimize` or `-o`)
  - Builds the lexer/parser with PLY’s optimization flag, which can improve parsing speed.
  - Use the flag to build with optimization: `python lexerTester.py -o` or `python parserTester.py --optimize`.

- **Heavy Mode** (`--heavy` or `-h`)
  - Runs a performance stress test (only applicable to the lexer tester). It repeatedly tokenizes a large test file to measure execution time.
  - Activate with `python lexerTester.py --heavy`.

These options can be combined, e.g., `python lexerTester.py -v -o --heavy`.

## Setup and Requirements

The project uses a Python virtual environment. To get started:

```bash
python -m venv .venv
source .venv/bin/activate   # on Unix/macOS
# .venv\Scripts\activate   # on Windows

pip install -r requirements.txt
```

The `requirements.txt` file was generated from the virtual environment and contains all necessary dependencies (e.g., PLY, tabulate). After activation, you can run the lexer, parser, and tests as described above.

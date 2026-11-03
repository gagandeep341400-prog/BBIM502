"""Controlled tests for the 11 exception types named in BBIM502 Assessment 2.

Run with: python exception_handling_coverage.py
These probes are isolated test cases. They do not intentionally damage the
hotel application's data or introduce syntax errors into langham_hotel.py.
"""
from __future__ import annotations

import importlib
import math
import tempfile
from pathlib import Path
from unittest.mock import patch
from typing import Callable, Type


def _test_case(label: str, operation: Callable[[], object],
               expected: Type[BaseException]) -> tuple[str, bool]:
    """Run one controlled operation and catch its expected exception."""
    try:
        operation()
    except expected as exc:
        return (f"PASS | {label}: caught {type(exc).__name__}", True)
    except Exception as exc:  # Report a wrong exception type, not a false pass.
        return (f"FAIL | {label}: expected {expected.__name__}, got {type(exc).__name__}", False)
    return (f"FAIL | {label}: the expected {expected.__name__} was not raised", False)


def _raise_io_error() -> None:
    # Python 3 defines IOError as an alias of OSError; this exercises that handler.
    raise IOError("controlled I/O failure for the exception test")


def _raise_eof_error() -> object:
    with patch("builtins.input", side_effect=EOFError("end of input")):
        return input("Controlled input test: ")


def run_checks() -> list[tuple[str, bool]]:
    """Run safe, isolated probes for all 11 requested exception types."""
    with tempfile.TemporaryDirectory(prefix="lhms_exception_tests_") as temp_dir:
        missing_file = Path(temp_dir) / "file_that_does_not_exist.txt"
        probes: list[tuple[str, Callable[[], object], Type[BaseException]]] = [
            ("SyntaxError", lambda: compile("print('unterminated)", "controlled_test.py", "exec"), SyntaxError),
            ("ValueError", lambda: int("not-a-number"), ValueError),
            ("ZeroDivisionError", lambda: 1 / 0, ZeroDivisionError),
            ("IndexError", lambda: [][0], IndexError),
            ("NameError", lambda: eval("lhms_name_that_is_not_defined"), NameError),
            ("TypeError", lambda: "room" + 1, TypeError),
            ("OverflowError", lambda: math.exp(10000), OverflowError),
            ("IOError", _raise_io_error, IOError),
            ("ImportError", lambda: importlib.import_module("lhms_module_that_does_not_exist_for_test"), ImportError),
            ("EOFError", _raise_eof_error, EOFError),
            ("FileNotFoundError", lambda: missing_file.open("r", encoding="utf-8"), FileNotFoundError),
        ]
        return [_test_case(label, operation, expected) for label, operation, expected in probes]


def main() -> int:
    """Print pass/fail results and return a non-zero exit code on failure."""
    print("BBIM502 — Controlled Exception Handling Checks")
    print("These checks run isolated test cases; application data is not changed.\n")
    results = run_checks()
    for line, _passed in results:
        print(line)
    passed = sum(1 for _line, ok in results if ok)
    failed = len(results) - passed
    print(f"\nResult: {passed}/{len(results)} exception probes passed; {failed} failed.")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

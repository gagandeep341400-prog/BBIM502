"""Verify the main menu's exception handlers catch each requested exception."""
from __future__ import annotations

import contextlib
import io
import unittest
from unittest.mock import patch

import langham_hotel as app


class MainExceptionHandlerTests(unittest.TestCase):
    def test_main_catches_requested_exceptions_at_menu_boundary(self) -> None:
        cases = [
            (SyntaxError("controlled"), "Syntax-related operation failed safely"),
            (ValueError("controlled"), "Invalid value"),
            (ZeroDivisionError("controlled"), "division by zero"),
            (IndexError("controlled"), "sequence index"),
            (NameError("controlled"), "not defined"),
            (TypeError("controlled"), "incompatible data type"),
            (OverflowError("controlled"), "exceeded its supported range"),
            (IOError("controlled"), "file or operating-system operation failed"),
            (ImportError("controlled"), "could not be imported"),
            (FileNotFoundError("controlled"), "required file was not found"),
        ]
        original_dispatch = app._dispatch
        for exception, expected_text in cases:
            with self.subTest(exception=type(exception).__name__):
                output = io.StringIO()

                def dispatch(choice: int, caught=exception):
                    if choice == 1:
                        raise caught
                    return original_dispatch(choice)

                with patch("builtins.input", side_effect=["1", "0"]), \
                     patch.object(app, "_dispatch", side_effect=dispatch), \
                     contextlib.redirect_stdout(output):
                    app.main()
                self.assertIn(expected_text, output.getvalue())
                self.assertIn("Thank you for using", output.getvalue())

    def test_main_catches_eoferror_from_input(self) -> None:
        output = io.StringIO()
        with patch("builtins.input", side_effect=EOFError), contextlib.redirect_stdout(output):
            app.main()
        self.assertIn("Input ended. Application closed safely.", output.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)

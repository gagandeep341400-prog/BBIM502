"""Automated regression tests for the Langham Hotel Management System."""
from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import langham_hotel as app
from exception_handling_coverage import run_checks


class HotelManagementTests(unittest.TestCase):
    def setUp(self) -> None:
        app.ROOMS.clear()
        app.ALLOCATIONS.clear()
        self.temp_dir = tempfile.TemporaryDirectory(prefix="lhms_app_tests_")
        self.old_app_dir = app.APP_DIR
        self.old_data_file = app.DATA_FILE
        app.APP_DIR = Path(self.temp_dir.name)
        app.DATA_FILE = app.APP_DIR / "LHMS_TestStudent.txt"

    def tearDown(self) -> None:
        app.APP_DIR = self.old_app_dir
        app.DATA_FILE = self.old_data_file
        self.temp_dir.cleanup()

    def _inputs(self, values: list[str], function) -> str:
        output = io.StringIO()
        with patch("builtins.input", side_effect=values), contextlib.redirect_stdout(output):
            function()
        return output.getvalue()

    def test_add_rooms_and_keep_existing_rooms(self) -> None:
        self._inputs(["1", "101", "Standard room, queen bed and ensuite"], app.add_rooms)
        self._inputs(["1", "102", "Deluxe room, king bed and city view"], app.add_rooms)
        self.assertEqual(set(app.ROOMS), {101, 102})
        self.assertIn("features", app.ROOMS[101])

    def test_duplicate_room_number_is_rejected(self) -> None:
        self._inputs(["2", "101", "Standard room", "101", "102", "Deluxe room"], app.add_rooms)
        self.assertEqual(set(app.ROOMS), {101, 102})

    def test_allocation_rejects_existing_customer_id(self) -> None:
        app.ROOMS.update({101: {"allocated": False}, 102: {"allocated": False}})
        app.ALLOCATIONS[101] = {"room_no": 101, "customer_id": 77, "customer_name": "A",
                                "nights": 1, "rate": 10, "allocated_at": "test"}
        app.ROOMS[101]["allocated"] = True
        output = self._inputs(["102", "B", "77", "78", "2", "100"], app.allocate_rooms)
        self.assertIn("already has an active room allocation", output)
        self.assertEqual(app.ALLOCATIONS[102]["customer_id"], 78)

    def test_billing_calculates_tax_and_releases_room(self) -> None:
        app.ROOMS[101] = {"allocated": True}
        app.ALLOCATIONS[101] = {"room_no": 101, "customer_id": 77, "customer_name": "Test Guest",
                                "nights": 3, "rate": 100, "allocated_at": "test"}
        output = self._inputs(["101"], app.billing_and_deallocate)
        self.assertIn("Subtotal: NZD 300.00", output)
        self.assertIn("GST (15%): NZD 45.00", output)
        self.assertIn("Total due: NZD 345.00", output)
        self.assertFalse(app.ROOMS[101]["allocated"])
        self.assertNotIn(101, app.ALLOCATIONS)

    def test_cannot_delete_allocated_room(self) -> None:
        app.ROOMS[101] = {"allocated": True}
        app.ALLOCATIONS[101] = {"room_no": 101, "customer_id": 77, "customer_name": "A",
                                "nights": 1, "rate": 10, "allocated_at": "test"}
        output = self._inputs(["101"], app.delete_room)
        self.assertIn("This room is allocated", output)
        self.assertIn(101, app.ROOMS)

    def test_save_file_is_valid_json_and_overwrites_old_contents(self) -> None:
        app.ROOMS[101] = {"allocated": False}
        app.DATA_FILE.write_text("stale old content that should be removed", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            app.save_allocations()
        saved = json.loads(app.DATA_FILE.read_text(encoding="utf-8"))
        self.assertIn("101", saved["rooms"])
        self.assertNotIn("stale old content", app.DATA_FILE.read_text(encoding="utf-8"))

    def test_missing_allocation_file_is_handled(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            app.show_allocations_from_file()
        self.assertIn("was not found", output.getvalue())

    def test_backup_copies_content_and_clears_source(self) -> None:
        app.DATA_FILE.write_text("test allocation record\n", encoding="utf-8")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            app.backup_and_clear_file()
        backups = list(Path(app.APP_DIR).glob("LHMS_Studentid_Backup_*.txt"))
        # Backup name follows STUDENT_ID; in this test STUDENT_ID is the default placeholder.
        self.assertTrue(backups)
        self.assertIn("test allocation record", backups[0].read_text(encoding="utf-8"))
        self.assertEqual(app.DATA_FILE.read_text(encoding="utf-8"), "")

    def test_all_eleven_exception_probes_pass(self) -> None:
        results = run_checks()
        self.assertEqual(len(results), 11)
        self.assertTrue(all(ok for _line, ok in results), "\n".join(line for line, ok in results if not ok))


if __name__ == "__main__":
    unittest.main(verbosity=2)

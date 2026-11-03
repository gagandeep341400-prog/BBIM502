"""Langham Hotel Management System.

Course: BBIM502 Introduction to Programming — Assessment 2
Author: Replace with your name before submission.
Description: Console-based room management, booking, billing and file I/O.
Date: 24 October 2026

The project uses only the Python standard library.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

# Replace the placeholder with your actual student ID before submitting.
STUDENT_ID = "Studentid"
GST_RATE = 0.15  # Demonstration assumption; confirm against course instructions.
APP_DIR = Path(__file__).resolve().parent
DATA_FILE = APP_DIR / f"LHMS_{STUDENT_ID}.txt"

ROOMS: dict[int, dict[str, Any]] = {}
ALLOCATIONS: dict[int, dict[str, Any]] = {}


def read_int(prompt: str, minimum: int | None = None,
             maximum: int | None = None) -> int:
    """Read an integer and retry for invalid values or values out of range.

    EOFError is deliberately allowed to reach main(), which closes the
    application cleanly instead of looping forever when input has ended.
    """
    while True:
        try:
            value = int(input(prompt).strip())
        except ValueError:
            print("Invalid input. Please enter a whole number.")
            continue

        if minimum is not None and value < minimum:
            print(f"Enter a number greater than or equal to {minimum}.")
            continue
        if maximum is not None and value > maximum:
            print(f"Enter a number no greater than {maximum}.")
            continue
        return value


def read_text(prompt: str) -> str:
    """Read non-empty text; allow EOFError to be handled by main()."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("This field cannot be empty.")


def add_rooms() -> None:
    """Add unique room numbers without removing rooms already registered."""
    count = read_int("How many rooms would you like to add? ", 1, 500)
    added = 0
    while added < count:
        room_no = read_int(f"Enter room number ({added + 1}/{count}): ", 1)
        if room_no in ROOMS:
            print("That room number already exists. Try another.")
            continue
        features = read_text("Enter room features (e.g., queen bed, ensuite, Wi-Fi): ")
        ROOMS[room_no] = {"allocated": False, "features": features}
        added += 1
        print(f"Room {room_no} added successfully.")


def delete_room() -> None:
    """Delete an existing room only if it has no active allocation."""
    if not ROOMS:
        print("No rooms exist. Add rooms first.")
        return
    room_no = read_int("Enter room number to delete: ", 1)
    if room_no not in ROOMS:
        print("Room not found.")
    elif ROOMS[room_no]["allocated"]:
        print("This room is allocated. Bill and release it before deleting.")
    else:
        del ROOMS[room_no]
        print(f"Room {room_no} deleted successfully.")


def display_rooms() -> None:
    """Display each registered room and its current availability."""
    if not ROOMS:
        print("No rooms available. Please add rooms first.")
        return
    print("\nROOM DETAILS")
    print(f"{'Room No.':<12}{'Status':<12}{'Feature'}")
    for room_no, room in sorted(ROOMS.items()):
        status = "Allocated" if room["allocated"] else "Available"
        features = room.get("features", "Not recorded in this room record")
        print(f"{room_no:<12}{status:<12}{features}")


def _new_customer_id() -> int:
    """Request a positive customer ID that is not currently in use."""
    while True:
        customer_id = read_int("Enter customer number: ", 1)
        if any(record["customer_id"] == customer_id
               for record in ALLOCATIONS.values()):
            print("That customer number already has an active room allocation.")
            continue
        return customer_id


def allocate_rooms() -> None:
    """Allocate an available room and store its customer and stay details."""
    available = [n for n, room in ROOMS.items() if not room["allocated"]]
    if not available:
        print("No available rooms. Add rooms or release an allocated room.")
        return

    print("Available rooms:", ", ".join(map(str, sorted(available))))
    room_no = read_int("Enter room number to allocate: ", 1)
    if room_no not in ROOMS:
        print("Room not found. Add the room before allocating it.")
        return
    if ROOMS[room_no]["allocated"]:
        print("That room is already allocated.")
        return

    customer_name = read_text("Enter customer name: ")
    customer_id = _new_customer_id()
    nights = read_int("Number of nights: ", 1, 365)
    rate = read_int("Room rate per night (NZD): ", 0, 1_000_000)
    ALLOCATIONS[room_no] = {
        "room_no": room_no,
        "customer_id": customer_id,
        "customer_name": customer_name,
        "nights": nights,
        "rate": rate,
        "allocated_at": datetime.now().isoformat(timespec="seconds"),
    }
    ROOMS[room_no]["allocated"] = True
    print(f"Room {room_no} allocated to {customer_name} successfully.")


def display_allocations() -> None:
    """Display details for all current room allocations."""
    if not ALLOCATIONS:
        print("There are no current room allocations.")
        return
    print("\nCURRENT ROOM ALLOCATIONS")
    print(f"{'Room':<8}{'Customer ID':<14}{'Customer':<24}{'Nights':<8}{'Rate/Night':<13}")
    for room_no, item in sorted(ALLOCATIONS.items()):
        print(f"{room_no:<8}{item['customer_id']:<14}{item['customer_name']:<24}"
              f"{item['nights']:<8}{item['rate']:<13}")


def billing_and_deallocate() -> None:
    """Calculate and show a bill, then release an allocated room."""
    if not ALLOCATIONS:
        print("No room allocations are available for billing.")
        return
    room_no = read_int("Enter room number to bill and release: ", 1)
    if room_no not in ALLOCATIONS:
        print("No active allocation exists for that room.")
        return

    item = ALLOCATIONS[room_no]
    subtotal = item["nights"] * item["rate"]
    tax = round(subtotal * GST_RATE, 2)
    total = subtotal + tax
    print("\nLANGHAM HOTELS - BILL")
    print(f"Customer: {item['customer_name']} (#{item['customer_id']})")
    print(f"Room: {room_no} | Nights: {item['nights']} | Rate: NZD {item['rate']:.2f}")
    print(f"Subtotal: NZD {subtotal:.2f}")
    print(f"GST ({GST_RATE:.0%}): NZD {tax:.2f}")
    print(f"Total due: NZD {total:.2f}")

    # Update both collections together after the bill has been displayed.
    del ALLOCATIONS[room_no]
    if room_no in ROOMS:
        ROOMS[room_no]["allocated"] = False
    print(f"Room {room_no} has been released and is available again.")


def _serializable_state() -> dict[str, Any]:
    """Build a JSON-safe text snapshot of all rooms and active allocations."""
    return {
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "student_id": STUDENT_ID,
        "rooms": {str(key): value for key, value in ROOMS.items()},
        "allocations": {str(key): value for key, value in ALLOCATIONS.items()},
    }


def save_allocations() -> None:
    """Create or overwrite the text file with the current application state."""
    try:
        # 'w' creates a missing file and truncates an old file before writing.
        with DATA_FILE.open("w", encoding="utf-8") as file:
            json.dump(_serializable_state(), file, indent=2, ensure_ascii=False)
            file.write("\n")
        print(f"Room allocation data saved to: {DATA_FILE.name}")
    except OSError as exc:
        print(f"Unable to save allocation file: {exc}")


def show_allocations_from_file() -> None:
    """Read, display, and close the saved room allocation text file."""
    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            content = file.read()
        if not content.strip():
            print("The allocation file is empty.")
            return
        print("\nSAVED ROOM ALLOCATION DATA")
        print(content)
    except FileNotFoundError:
        print(f"File {DATA_FILE.name} was not found. Choose option 7 first.")
    except (OSError, UnicodeError) as exc:
        print(f"Unable to read allocation file: {exc}")


def backup_and_clear_file() -> None:
    """Append the saved text to a timestamped backup and clear the source file."""
    try:
        if not DATA_FILE.exists():
            print(f"File {DATA_FILE.name} was not found. Choose option 7 first.")
            return
        content = DATA_FILE.read_text(encoding="utf-8")
        # Microseconds prevent two backups in the same second overwriting names.
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_file = APP_DIR / f"LHMS_{STUDENT_ID}_Backup_{timestamp}.txt"
        with backup_file.open("a", encoding="utf-8") as file:
            file.write(content)
            if content and not content.endswith("\n"):
                file.write("\n")
        # Only clear the source after the backup write completed successfully.
        with DATA_FILE.open("w", encoding="utf-8") as file:
            file.write("")
        print(f"Backup created: {backup_file.name}")
        print(f"{DATA_FILE.name} has been cleared.")
    except FileNotFoundError as exc:
        print(f"Required file was not found: {exc}")
    except (OSError, UnicodeError) as exc:
        print(f"Backup or clear operation failed: {exc}")


def print_menu() -> None:
    """Print all ten application menu choices required by the assessment."""
    print("\n" + "=" * 64)
    print("             LANGHAM HOTEL MANAGEMENT SYSTEM")
    print("=" * 64)
    print("1. Add Room")
    print("2. Delete Room")
    print("3. Display Rooms Details")
    print("4. Allocate Room")
    print("5. Display Room Allocation Details")
    print("6. Billing and De-allocation")
    print("7. Save Room Allocation to a File")
    print("8. Display Room Allocation from a File")
    print("9. Backup and Clear Room Allocation File")
    print("0. Exit")
    print("=" * 64)


def _dispatch(choice: int) -> None:
    """Run the selected menu operation using a validated menu number."""
    actions = {
        1: add_rooms,
        2: delete_room,
        3: display_rooms,
        4: allocate_rooms,
        5: display_allocations,
        6: billing_and_deallocate,
        7: save_allocations,
        8: show_allocations_from_file,
        9: backup_and_clear_file,
    }
    if choice == 0:
        print("Thank you for using Langham Hotel Management System.")
        return
    action = actions.get(choice)
    if action is None:
        print("Invalid menu option. Enter a number from 0 to 9.")
        return
    action()


def main() -> None:
    """Run the console menu until exit or end-of-input is received."""
    while True:
        try:
            print_menu()
            choice = read_int("Enter menu option (0-9): ", 0, 9)
            if choice == 0:
                _dispatch(choice)
                break
            _dispatch(choice)
        except EOFError:
            print("\nInput ended. Application closed safely.")
            break
        except KeyboardInterrupt:
            print("\nApplication interrupted. Closing safely.")
            break
        except SyntaxError as exc:
            # SyntaxError is uncommon during normal menu use; this protects
            # against invalid dynamically compiled content if later added.
            print(f"Syntax-related operation failed safely: {exc}")
        except ImportError as exc:
            print(f"A required module could not be imported: {exc}")
        except ValueError as exc:
            print(f"Invalid value: {exc}")
        except ZeroDivisionError as exc:
            print(f"A calculation attempted division by zero: {exc}")
        except IndexError as exc:
            print(f"A sequence index was outside its valid range: {exc}")
        except NameError as exc:
            print(f"A required variable or name was not defined: {exc}")
        except TypeError as exc:
            print(f"An operation received an incompatible data type: {exc}")
        except OverflowError as exc:
            print(f"A numeric operation exceeded its supported range: {exc}")
        except FileNotFoundError as exc:
            print(f"A required file was not found: {exc}")
        except OSError as exc:
            # IOError is an alias of OSError in Python 3.
            print(f"A file or operating-system operation failed: {exc}")
        except Exception as exc:
            # Final guard ensures an unforeseen runtime error is reported cleanly.
            print(f"Unexpected operation error ({type(exc).__name__}): {exc}")


if __name__ == "__main__":
    main()

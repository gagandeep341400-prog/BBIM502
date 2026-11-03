"""Generate reproducible console-output captures from the running application.

These images render output captured from actual function/menu executions with
scripted sample input. They are not screenshots of a personal Windows desktop.
"""
from __future__ import annotations

import contextlib
import io
import tempfile
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw, ImageFont
import langham_hotel as app

ROOT = Path(__file__).resolve().parent
SCREENSHOT_DIR = ROOT / "screenshots"
LOG_DIR = SCREENSHOT_DIR / "captured_output"
BG = (16, 16, 16)
FG = (204, 230, 206)
BAR = (43, 43, 43)
MUTED = (190, 190, 190)


def font(size: int):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf",
        "C:/Windows/Fonts/consola.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def capture(label: str, function, inputs: list[str] | None = None, setup=None) -> str:
    app.ROOMS.clear()
    app.ALLOCATIONS.clear()
    with tempfile.TemporaryDirectory(prefix="lhms_capture_") as temp_dir:
        old_app_dir, old_data_file = app.APP_DIR, app.DATA_FILE
        try:
            app.APP_DIR = Path(temp_dir)
            app.DATA_FILE = app.APP_DIR / f"LHMS_{app.STUDENT_ID}.txt"
            if setup:
                setup()
            output = io.StringIO()
            if inputs is None:
                with contextlib.redirect_stdout(output):
                    function()
            else:
                responses = iter(inputs)
                def echoed_input(prompt: str = "") -> str:
                    # A terminal echoes typed responses after displaying prompts.
                    output.write(prompt)
                    try:
                        response = next(responses)
                    except StopIteration as exc:
                        raise EOFError("No more scripted input") from exc
                    output.write(response + "\n")
                    return response
                with patch("builtins.input", side_effect=echoed_input), contextlib.redirect_stdout(output):
                    function()
            content = output.getvalue().rstrip() or "(No console output.)"
            (LOG_DIR / f"{label}.txt").write_text(content + "\n", encoding="utf-8")
            render_terminal_image(label, content, SCREENSHOT_DIR / f"{label}.png")
            return content
        finally:
            app.APP_DIR, app.DATA_FILE = old_app_dir, old_data_file


def render_terminal_image(label: str, content: str, destination: Path) -> None:
    lines = content.splitlines() or [""]
    terminal_font = font(18)
    header_font = font(15)
    line_height = 27
    width = min(1500, max(900, max(len(line) for line in lines) * 11 + 40))
    max_chars = max(30, (width - 36) // 11)
    # Wrap very long JSON/text lines to keep the screenshot readable.
    wrapped: list[str] = []
    for line in lines:
        if len(line) <= max_chars:
            wrapped.append(line)
        else:
            while len(line) > max_chars:
                wrapped.append(line[:max_chars])
                line = "    " + line[max_chars:]
            wrapped.append(line)
    height = min(2200, max(120, 42 + len(wrapped) * line_height + 18))
    image = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, 38), fill=BAR)
    draw.text((14, 10), f"Command Prompt — Langham Hotel Management System — {label}", font=header_font, fill=MUTED)
    y = 52
    for line in wrapped[:(height - 54) // line_height]:
        draw.text((18, y), line, font=terminal_font, fill=FG)
        y += line_height
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination)


def main() -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    capture("menu", app.print_menu)
    capture("option1_add_rooms", app.add_rooms, ["2", "101", "Standard room, queen bed and ensuite", "102", "Deluxe room, king bed and city view"])

    def rooms_for_delete():
        app.ROOMS.update({101: {"allocated": False, "features": "Standard room, queen bed and ensuite"}, 102: {"allocated": False, "features": "Deluxe room, king bed and city view"}})
    capture("option2_delete_room", app.delete_room, ["102"], rooms_for_delete)

    def rooms_for_display():
        app.ROOMS.update({101: {"allocated": False, "features": "Standard room, queen bed and ensuite"}, 102: {"allocated": True, "features": "Deluxe room, king bed and city view"}})
    capture("option3_display_rooms", app.display_rooms, setup=rooms_for_display)

    def room_for_allocation():
        app.ROOMS[101] = {"allocated": False}
    capture("option4_allocate_room", app.allocate_rooms,
            ["101", "Alex Morgan", "9001", "2", "100"], room_for_allocation)

    def active_allocation():
        app.ROOMS[101] = {"allocated": True}
        app.ALLOCATIONS[101] = {
            "room_no": 101, "customer_id": 9001, "customer_name": "Alex Morgan",
            "nights": 2, "rate": 100, "allocated_at": "2026-10-24T13:00:00"
        }
    capture("option5_allocation_details", app.display_allocations, setup=active_allocation)
    capture("option6_billing", app.billing_and_deallocate, ["101"], active_allocation)
    capture("option7_save_file", app.save_allocations, setup=active_allocation)

    def saved_allocation_file():
        active_allocation()
        app.save_allocations()
    capture("option8_display_file", app.show_allocations_from_file, setup=saved_allocation_file)
    capture("option9_backup_clear", app.backup_and_clear_file,
            setup=saved_allocation_file)

    # Capture the real menu/exit path through main() with a controlled input.
    with tempfile.TemporaryDirectory(prefix="lhms_exit_capture_") as temp_dir:
        old_app_dir, old_data_file = app.APP_DIR, app.DATA_FILE
        try:
            app.APP_DIR = Path(temp_dir)
            app.DATA_FILE = app.APP_DIR / f"LHMS_{app.STUDENT_ID}.txt"
            output = io.StringIO()
            def echoed_exit_input(prompt: str = "") -> str:
                output.write(prompt + "0\n")
                return "0"
            with patch("builtins.input", side_effect=echoed_exit_input), contextlib.redirect_stdout(output):
                app.main()
            content = output.getvalue().rstrip()
            (LOG_DIR / "option0_exit.txt").write_text(content + "\n", encoding="utf-8")
            # The exit image shows the menu and the exit confirmation from the actual main() run.
            render_terminal_image("option0_exit", content, SCREENSHOT_DIR / "option0_exit.png")
        finally:
            app.APP_DIR, app.DATA_FILE = old_app_dir, old_data_file

    # Exception probe output is also captured from the live controlled-test script.
    import exception_handling_coverage
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        result_code = exception_handling_coverage.main()
    text = out.getvalue().rstrip()
    (LOG_DIR / "exception_handling_11_types.txt").write_text(text + "\n", encoding="utf-8")
    render_terminal_image("exception_handling_11_types", text,
                          SCREENSHOT_DIR / "exception_handling_11_types.png")
    if result_code:
        raise SystemExit(result_code)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Verify EarthBound: Zero Fault compiled ROM binary integrity and injected hooks.
"""

import os
import sys

ROM_PATH = "build/eb_zero_fault.sfc"
EXPECTED_SIZE = 4_194_304  # 32 Mbits (4 MB)

HOOKS = [
    # Dash hooks (0xC02F30, 0xC031B8, 0xC07960)
    (0x002F30, b"\x22", "Dash Hook 1 (Movement Vector)"),
    (0x0031B8, b"\x22", "Dash Hook 2 (Diagonal Vector)"),
    (0x007960, b"\x22", "Dash Hook 3 (Movement Normalization)"),
    # Fast text hooks
    (0x01FEC9, b"\x22", "Fast Text Hook 1 (Delay Calculation)"),
    (0x010D4B, b"\x22", "Fast Text Hook 2 (Delay Check Call 1)"),
    (0x044055, b"\x22", "Fast Text Hook 3 (Delay Check Call 2)"),
    (0x0444E3, b"\x22", "Fast Text Hook 4 (Delay Check Call 3)"),
    (0x02038B, b"\x5C", "Fast Text Battle HDMA Queue Guard"),
    # Shop stat comparison hooks
    (0x05E277, b"\x0A", "Shop Equipment Stat Display Part 1"),
    (0x05E2F7, b"\x0A", "Shop Equipment Stat Display Part 2"),
    # Phase 4: CoW Narrative & MMU Hooks
    (0x074F56, b"\x0A", "CoW Mom Awakening Script Hook"),
    (0x075C33, b"\x0A", "CoW Pokey Front Door Burst Hook"),
    (0x072AF8, b"\x0A", "CoW Mayor Pirkle Refcount Hook"),
    (0x066002, b"\x0A", "CoW Twoson MMU Roadblock Hook"),
    (0x07BEB9, b"\x0A", "CoW Giant Step Cache Commit Hook"),
]

# EarthBound standard text byte mappings (A-Z = 0x71-0x8A, a-z = 0x91-0xAA, space = 0x50)
def eb_encode(text: str) -> bytes:
    res = bytearray()
    for ch in text:
        if ch == " ":
            res.append(0x50)
        elif "A" <= ch <= "Z":
            res.append(ord(ch) + 0x30)
        elif "a" <= ch <= "z":
            res.append(ord(ch) + 0x30)
        elif "0" <= ch <= "9":
            res.append(ord(ch) + 0x30)
        else:
            res.append(ord(ch))
    return bytes(res)


THEMATIC_NAMES = [
    "The OOM Killer",
    "Null Reference Crow",
    "Dangling Pointer",
    "Runaway Thread",
    "Fork Bomb",
    "Dirty Page",
]


def main() -> int:
    if not os.path.isfile(ROM_PATH):
        print(f"ERROR: ROM not found at {ROM_PATH}. Run tools/build.sh first.")
        return 1

    size = os.path.getsize(ROM_PATH)
    if size != EXPECTED_SIZE:
        print(f"ERROR: Invalid ROM size {size} bytes (expected {EXPECTED_SIZE}).")
        return 1

    errors = 0
    with open(ROM_PATH, "rb") as f:
        rom_data = f.read()

        # Check HiROM SNES title at 0xFFC0
        f.seek(0xFFC0)
        title = f.read(21)
        if title != b"EARTH BOUND          ":
            print(f"ERROR: Unexpected internal title: {title!r}")
            errors += 1
        else:
            print(f"OK: Internal SNES Title: {title.decode('latin1').strip()}")

        for offset, expected_prefix, description in HOOKS:
            f.seek(offset)
            actual = f.read(len(expected_prefix))
            if actual != expected_prefix:
                print(
                    f"ERROR: Hook mismatch for {description} at {hex(offset)}: "
                    f"expected {expected_prefix.hex()}, found {actual.hex()}"
                )
                errors += 1
            else:
                print(f"OK: {description} verified at {hex(offset)}")

        for name in THEMATIC_NAMES:
            encoded = eb_encode(name)
            if encoded in rom_data:
                print(f"OK: Thematic string '{name}' verified in ROM")
            else:
                print(f"ERROR: Thematic string '{name}' not found in ROM")
                errors += 1

    total_checks = 1 + len(HOOKS) + len(THEMATIC_NAMES)
    if errors == 0:
        print(f"\nAll {total_checks} binary assertions passed successfully.")
        return 0
    else:
        print(f"\nVerification failed with {errors} error(s).")
        return 1


if __name__ == "__main__":
    sys.exit(main())

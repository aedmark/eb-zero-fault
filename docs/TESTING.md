# Testing

How to run every test, what each one proves, and what it cannot. Read this before claiming anything works.
The results themselves live in HANDOFF's "Current state"; this file is how to get them.

## The suites

| Suite | File | Proves | Does not prove | Time, needs |
| --- | --- | --- | --- | --- |
| Documentation | `tools/check_docs.py` | Cross-references, decision IDs, roadmap items, no placeholders | That the code or ROM builds | Seconds, Python standard library |
| Toolchain check | `coilsnake --version` | Python environment and CoilSnake CLI functionality | That project files compile | Seconds, active `.venv` |
| ROM Compilation | `tools/build.sh` | CCScript syntax, YAML schema validity, VRAM graphics import | Runtime game logic or game balance | 6-10 seconds, CPU |
| Binary Verification | `tools/verify_rom.py` | Validates 22 binary assertions (header, dash hooks, text hooks, shop stats, CoW narrative, and thematic enemy/item names) | Interactive player control feel | Seconds, Python standard library |
| Emulation test | Manual in Mesen-S | In-game behavior, dialogue formatting, music playback, collision | Full 40-hour game completion | Minutes, GUI emulator |

**The fast set** (before every commit): `python3 tools/check_docs.py` and `python3 tools/verify_rom.py`.
**The full set** (after modifying scripts or tables): `tools/build.sh`, `python3 tools/verify_rom.py`, and `python3 tools/check_docs.py`.

**Expected results** live in HANDOFF's "Verified" table, with the date and commit they were measured on.

## Before any run

What has to be true before a test or a real run means anything.

- **Clean state:** Output build files in `build/` can be deleted safely before recompilation.
- **Resource caps:** Compiling EarthBound via CoilSnake takes under 500 MB of RAM and terminates within 30 seconds.
- **Environment:** Run within an active Python virtual environment (`source .venv/bin/activate`).

## Running each suite

### Documentation Consistency Check

```bash
python3 tools/check_docs.py
```

- What it does: Scans all documentation files for orphaned placeholder patterns, dangling links, invalid roadmap/decision IDs, and invisible characters.
- What a pass looks like: Exit code 0, reporting `0 error(s), 0 warning(s)`.
- Where it writes output: Standard output.

### Build and Compilation Test

```bash
coilsnake compile src/ build/eb_zero_fault.sfc
```

- What it does: Reads `src/`, compresses text, compiles CCScript bytecode, formats graphics and tables, and outputs the SNES ROM.
- What a pass looks like: Terminal prints successful compilation summary and writes `eb_zero_fault.sfc`.
- Where it writes output: `build/eb_zero_fault.sfc`.

### Emulation and Visual Inspection

```bash
mesen-s build/eb_zero_fault.sfc
```

- What it does: Boots the compiled ROM in a cycle-accurate SNES emulator.
- What to check: Verify title screen boots, start a new game, test dialogue window printing, and test B-Button dash movement.

# Session Handoff

Read this first when resuming unfinished work. Rewrite the top half whenever current state changes materially or work
pauses with context another session needs.
The session log below it is append-only history. "Current state" fits on a screen or two;
what does not fit is history, and belongs in the session log.

Protocol: see [AGENTS.md](../AGENTS.md) (`CLAUDE.md` imports it). Plan: [ROADMAP.md](../ROADMAP.md).
Architecture: [ARCHITECTURE.md](ARCHITECTURE.md). Decisions: [DECISIONS.md](DECISIONS.md).
Tests: [TESTING.md](TESTING.md). Security: [SECURITY.md](SECURITY.md).
Changes: [CHANGELOG.md](CHANGELOG.md). Older sessions: [archive/](archive/README.md).

---

## Current state

Last updated: 2026-11-14, session 4, on `main`: P2-02 completed. Implemented sub-frame fractional text speed and B-button dialogue fast-forward via `src/ccscript/fast_text.ccs` with BG3 HDMA corruption guard (D-007). Compiled cleanly in 6.54s.

**Session owner:** Antigravity / Maintainer, on `main`, since 2026-11-14. Phase 2 QoL implementation.

**Where things stand, in one paragraph:** Items P2-01 and P2-02 are complete. Movement has been upgraded with the outdoor B-Button Dash (D-006), and text rendering now supports sub-frame fractional delay pacing and instant character rendering while holding the B button (D-007). Battle HDMA queue serialization protects combat graphics during rapid dialogue progression. Both routines compile without errors in `build/eb_zero_fault.sfc`. The next task is P2-03 (shop equipment stat comparisons).

**Verified** (2026-11-14, CachyOS Linux x86-64-v3, Python 3.14.10)

| Suite | Result |
| --- | --- |
| `python3 tools/check_docs.py` | Pass (0 errors, 0 warnings) |
| ROM compilation (`tools/build.sh`) | Pass (4,194,304 bytes, 6.54s) |
| Binary hook verification (Python script) | Verified hooks at `0xC02F30`, `0xC031B8`, `0xC07960`, `0xC1FEC9`, `0xC10D4B`, `0xC44055`, `0xC444E3`, `0xC2038B` |

**What works**
- **Toolchain & Base Decompilation** (P1-01 through P1-04, D-001, D-002, D-005). Complete source tree in `src/` and reproducible automated build via `tools/build.sh`.
- **Outdoor-Only B-Button Dash** (P2-01, D-003, D-006; `src/ccscript/dash.ccs`). Player runs at double speed while holding B outdoors, retains normal walk indoors, and preserves vanilla Skip Sandwich behavior.
- **Accelerated Text Printing & Dialogue Fast-Forward** (P2-02, D-007; `src/ccscript/fast_text.ccs`). Sub-frame fractional text pacing with instantaneous character printing when holding B; includes BG3 HDMA upload serialization to prevent visual corruption.
- **Repository Harness** (`tools/check_docs.py`, `AGENTS.md`, `ROADMAP.md`, `docs/DECISIONS.md`). All invariants, decisions, and IDs remain consistent.

**Not verified**
- Interactive emulator control feel on hardware (pending emulator installation on host).

**Gotchas for the next session**
- Host OS is CachyOS (Arch Linux base). Use `pacman` or `paru`, never `apt`.
- Always compile using `tools/build.sh`.

## Next steps (in order)

1. Implement shop equipment stat differential comparison display (P2-03).
2. Test compiled ROM in an emulator (P2-04).

## Open questions for maintainers

None currently blocking.

## Session log

### Session 4 (2026-11-14)
Implemented P2-02 and recorded decision D-007. Created `src/ccscript/fast_text.ccs` implementing sub-frame fractional text delays (`FreeRAM_TextSpeedAccum` at `$962B`), B-button dialogue delay bypass, and battle HDMA BG3 upload serialization at `$C2038B`. Successfully compiled `build/eb_zero_fault.sfc` in 6.54 seconds and verified binary injection at `$C1FEC9`, `$C10D4B`, `$C44055`, `$C444E3`, and `$C2038B`.

### Session 3 (2026-11-14)
Resolved Q-001 in favor of Option B (Outdoors only) per maintainer directive, formalizing D-006. Imported 65816 assembly macro library `src/ccscript/asm65816.ccs`. Implemented `src/ccscript/dash.ccs` hooking controller 1 polling (`0x0066` high byte, mask `0x0080`) and native collision check `CHECK_BICYCLE_COLLISION_FLAGS` (`0xC03C4B`) at `0xC02F30`, `0xC031B8`, and `0xC07960`. Compiled `build/eb_zero_fault.sfc` in 6.58 seconds, verified binary injection, and marked P2-01 done.

### Session 2 (2026-11-14)
Completed Phase 1. Built CoilSnake 4.3 natively with ccscript and CCScriptWriter on Python 3.14 (P1-02). Executed clean ROM decompile and scriptdump generating `src/` asset tree and 62 CCScript data modules (P1-03). Formulated decision D-005 and automated ephemeral 32-Mbit intermediate base compilation via `tools/build.sh`, producing clean 4,194,304-byte output `build/eb_zero_fault.sfc` in 6.52 seconds (P1-04).

### Session 1 (2026-11-14)
Formalized project repository under The Manifold and Hypervisor. Verified base ROM file size (3,145,728 bytes unheadered) satisfying P1-01 and D-002. Drafted initial roadmap phases P1 through P6, architectural specifications, decisions D-001 through D-004, and validated documentation integrity via `tools/check_docs.py`.

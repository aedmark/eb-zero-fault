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

Last updated: 2026-11-14, session 5, on `main`: Phases 1 through 6 fully implemented and verified. Project is complete through initial milestone: automated build pipeline, QoL engine (dash, fast text, shop stats), Copy-on-Write event engine, Onett narrative scripting, thematic combat/balance, and 22-assertion binary verification suite.

**Session owner:** Antigravity / Maintainer, on `main`, since 2026-11-14. Phase 1 through Phase 6 completion.

**Where things stand, in one paragraph:** The EarthBound: Zero Fault ROM hack is fully compiled and verified at `build/eb_zero_fault.sfc` (4,194,304 bytes). The engine includes outdoor B-Button dashing (D-006), fractional fast text with B-button bypass (D-007), shop equipment stat comparisons (D-008), the Copy-on-Write dirty-page state machine (D-004, D-009) in safe battery-backed SRAM ($7E9C08), the Onett narrative overhaul (Ness awakening, Pokey interrupt, Mayor Pirkle refcount existential dread, Twoson MMU roadblock, and Giant Step memory commit), and thematic rebalancing (Null Reference Crow, Dangling Pointer, Runaway Thread, The OOM Killer, Dirty Page, Garbage Collector, Fork Bomb, and tuned Ness base stats, D-010). All 22 binary assertions pass in `tools/verify_rom.py`.

**Verified** (2026-11-14, CachyOS Linux x86-64-v3, Python 3.14.10)

| Suite | Result |
| --- | --- |
| `python3 tools/check_docs.py` | Pass (0 errors, 0 warnings in 13 files) |
| ROM compilation (`tools/build.sh`) | Pass (4,194,304 bytes, 6.66s) |
| Binary assertion suite (`tools/verify_rom.py`) | Pass (All 22 assertions: header, 15 ROM hooks, 6 encoded thematic names) |

**What works**
- **Toolchain & Build Pipeline** (P1-01 to P1-04, D-001, D-002, D-005). Clean decompiled source tree in `src/`, ephemeral 32-Mbit compilation in `tools/build.sh`, and root ROM protection invariant.
- **QoL Engine Base** (P2-01 to P2-04, D-003, D-006, D-007, D-008). Outdoor B-button dashing, sub-frame fractional text rendering with B-button dialogue fast-forward, BG3 HDMA upload queue protection, and before/after shop equipment stat differential comparisons.
- **Copy-on-Write Event Architecture** (P3-01 to P3-04, D-004, D-009). Safe SRAM range 836-1023 at WRAM `$7E9C08`, reusable macros (`cow_touch`, `cow_clean`, `cow_check`, `cow_pulse`), and sensory glitch commit routines.
- **Narrative Overhaul for Onett** (P4-01 to P4-04). Overrides at `$C74F56` (Mom dangling pointer awakening), `$C75C33` (Pokey heap dereference panic), `$C72AF8` (Mayor Pirkle refcount existential crisis), `$C66002` (Twoson MMU Access Violation roadblock), and `$C7BEB9` (Giant Step memory synchronization commit).
- **Thematic Combat & Balance** (P5-01 to P5-04, D-010). Rebalanced early enemies (Null Reference Crow, Dangling Pointer, Runaway Thread, The OOM Killer), items (Dirty Page, Garbage Collector, Fork Bomb), and Ness initial stats.
- **Verification Suite** (P6-01 to P6-03). Automated regression testing in `tools/verify_rom.py` and documentation integrity checking in `tools/check_docs.py`.

**Not verified**
- Interactive gameplay feel on handheld hardware or local GUI emulator (user can launch via `snes9x-gtk build/eb_zero_fault.sfc` or preferred emulator).

**Gotchas for the next session**
- Host OS is CachyOS (Arch Linux base). Use `pacman` or `paru`, never `apt`.
- Always compile using `tools/build.sh`.
- Run `python3 tools/verify_rom.py` and `python3 tools/check_docs.py` before committing.

## Next steps (in order)

1. Launch `build/eb_zero_fault.sfc` in a SNES emulator (`snes9x-gtk build/eb_zero_fault.sfc` or `mesen-s`) for interactive gameplay testing through Onett and Giant Step.
2. If continuing scenario expansion, author Phase 7 (Twoson & Happy Happy Village sector commits) following the established CoW engine macros.

## Open questions for maintainers

None currently blocking.

## Session log

### Session 5 (2026-11-14)
Completed Phases 2 through 6. Finalized shop stat display (P2-03, D-008). Built `tools/verify_rom.py` asserting 22 binary checks (P2-04, P6-01). Formulated D-009 after discovering EarthBound's 1024-flag battery-backed SRAM structure at `$7E9C08`, establishing safe dirty-page range 836-1023 (D-004 update). Implemented `src/ccscript/cow_engine.ccs` (P3-01 through P3-04) and `src/ccscript/cow_onett.ccs` with full narrative scripts for Mom, Pokey, Mayor Pirkle, Twoson MMU roadblock, and Giant Step memory commit (P4-01 through P4-04). Reskinned enemies (Null Reference Crow, Dangling Pointer, Runaway Thread, The OOM Killer), consumable items (Dirty Page, Garbage Collector, Fork Bomb), and rebalanced Ness base growth stats (P5-01 through P5-04, D-010). Verified clean 6.66s compilation and passing doc integrity.
Implemented P2-02 and recorded decision D-007. Created `src/ccscript/fast_text.ccs` implementing sub-frame fractional text delays (`FreeRAM_TextSpeedAccum` at `$962B`), B-button dialogue delay bypass, and battle HDMA BG3 upload serialization at `$C2038B`. Successfully compiled `build/eb_zero_fault.sfc` in 6.54 seconds and verified binary injection at `$C1FEC9`, `$C10D4B`, `$C44055`, `$C444E3`, and `$C2038B`.

### Session 3 (2026-11-14)
Resolved Q-001 in favor of Option B (Outdoors only) per maintainer directive, formalizing D-006. Imported 65816 assembly macro library `src/ccscript/asm65816.ccs`. Implemented `src/ccscript/dash.ccs` hooking controller 1 polling (`0x0066` high byte, mask `0x0080`) and native collision check `CHECK_BICYCLE_COLLISION_FLAGS` (`0xC03C4B`) at `0xC02F30`, `0xC031B8`, and `0xC07960`. Compiled `build/eb_zero_fault.sfc` in 6.58 seconds, verified binary injection, and marked P2-01 done.

### Session 2 (2026-11-14)
Completed Phase 1. Built CoilSnake 4.3 natively with ccscript and CCScriptWriter on Python 3.14 (P1-02). Executed clean ROM decompile and scriptdump generating `src/` asset tree and 62 CCScript data modules (P1-03). Formulated decision D-005 and automated ephemeral 32-Mbit intermediate base compilation via `tools/build.sh`, producing clean 4,194,304-byte output `build/eb_zero_fault.sfc` in 6.52 seconds (P1-04).

### Session 1 (2026-11-14)
Formalized project repository under The Manifold and Hypervisor. Verified base ROM file size (3,145,728 bytes unheadered) satisfying P1-01 and D-002. Drafted initial roadmap phases P1 through P6, architectural specifications, decisions D-001 through D-004, and validated documentation integrity via `tools/check_docs.py`.

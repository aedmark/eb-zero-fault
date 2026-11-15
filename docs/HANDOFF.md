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

Last updated: 2026-11-15, session 7, on `main`: Initial awakening dialogue hook (`0xC66D3E`) and overworld B-button status decoupling (`0xC0B8F1`) fully resolved (D-012). ROM is compiled and verified at `build/eb_zero_fault.sfc` (4,194,304 bytes) with 33 binary assertions passing.

**Session owner:** Antigravity / Maintainer, on `main`, since 2026-11-15. Root cause resolution for awakening dialogue and overworld dash modal freeze.

**Where things stand, in one paragraph:** The EarthBound: Zero Fault ROM hack is compiled and verified at `build/eb_zero_fault.sfc` (4,194,304 bytes). Resolved the unhooked initial dialogue anomaly by redirecting Mom's awakening text pointer at `$C66D3E` (Entry 15, flag 0x1d5 unset) to `cow_mom_initial_awakening` with sensory glitch pulse `{sound(11)}`, CoW state flags 850/870/840, and uninitialized pointer dialogue. Resolved the B-button modal lock by changing overworld status polling at `$C0B8F1` from `AND #$A000` to `AND #$2000` (Select button only), decoupling the B button from the blocking status loop at `$C13CA1` so B dashes cleanly without freezing movement. All 33 binary assertions pass in `tools/verify_rom.py`.

**Verified** (2026-11-15, CachyOS Linux x86-64-v3, Python 3.14.10)

| Suite | Result |
| --- | --- |
| `python3 tools/check_docs.py` | Pass (0 errors, 0 warnings in 13 files) |
| ROM compilation (`tools/build.sh`) | Pass (4,194,304 bytes, 6.56s) |
| Binary assertion suite (`tools/verify_rom.py`) | Pass (All 33 assertions: header, 23 ROM hooks, 9 encoded thematic names) |

**What works**
- **Toolchain & Build Pipeline** (P1-01 to P1-04, D-001, D-002, D-005). Clean decompiled source tree in `src/`, ephemeral 32-Mbit compilation in `tools/build.sh`, and root ROM protection invariant.
- **QoL Engine Base** (P2-01 to P2-04, D-003, D-006, D-007, D-008, D-012). Outdoor B-button dashing, overworld status window decoupling at `$C0B8F1` (Select only), sub-frame fractional text rendering with B-button dialogue fast-forward, BG3 HDMA upload queue protection, and before/after shop equipment stat differential comparisons.
- **Copy-on-Write Event Architecture** (P3-01 to P3-04, D-004, D-009). Safe SRAM range 836-1023 at WRAM `$7E9C08`, reusable macros (`cow_touch`, `cow_clean`, `cow_check`, `cow_pulse`), and sensory glitch commit routines.
- **Narrative Overhaul for Onett & Twoson** (P4-01 to P4-04, P7-01 to P7-03, D-011, D-012). Overrides at `$C66D3E` (Mom initial jammies awakening), `$C74F56` (Mom door knock awakening), `$C75C33` (Pokey heap panic), `$C72AF8` (Mayor Pirkle refcount dread), `$C66002` (Twoson MMU roadblock), `$C7BEB9` (Giant Step commit), `$C7699E` and `$C5F859` (Captain Strong kernel privilege audit), `$C81676` (Apple Kid JIT compiler), `$C95C0E` (Everdred raw heap allocator), `$C98024` (Carpainter Immutable Cult), and `$C7BF95` (Lilliput Steps cache commit).
- **Thematic Combat & Balance** (P5-01 to P5-04, P7-04, D-010, D-011). Rebalanced monsters (Null Reference Crow, Dangling Pointer, Runaway Thread, The OOM Killer, Runaway Linter, Deadlock Tree, Stack Overflow Mole), items (Dirty Page, Garbage Collector, Fork Bomb), and Ness initial stats.
- **Verification Suite** (P6-01 to P6-03). Automated regression testing in `tools/verify_rom.py` (33 assertions) and documentation integrity checking in `tools/check_docs.py`.

**Not verified**
- Interactive gameplay feel on handheld hardware or local GUI emulator (user can launch via `snes9x-gtk build/eb_zero_fault.sfc` or preferred emulator).

**Gotchas for the next session**
- Host OS is CachyOS (Arch Linux base). Use `pacman` or `paru`, never `apt`.
- Always compile using `tools/build.sh`.
- Run `python3 tools/verify_rom.py` and `python3 tools/check_docs.py` before committing.

## Next steps (in order)

1. Launch `build/eb_zero_fault.sfc` in a SNES emulator (`snes9x-gtk build/eb_zero_fault.sfc`) for interactive testing through Onett, Twoson, and Happy Happy Village.
2. Advance to Phase 8: Threed and Saturn Valley (Zombie process leaks, Fly Honey buffer overflow, Master Belch memory leak, and Milky Well cache commit).

## Open questions for maintainers

None currently blocking.

## Session log

### Session 7 (2026-11-15)
Diagnosed and resolved two runtime behavioral discrepancies reported during initial playtesting (D-012). First, identified that Mom before the meteorite event corresponds to NPC Entry 15 in `src/npc_config_table.yml` with text pointer `data_20.l_0xc66d3e` (`0xC66D3E`), which was running vanilla code because only Entry 14 (`0xC74F56`) had been hooked. Authored `cow_mom_initial_awakening` in `src/ccscript/cow_onett.ccs` and hooked `ROM[0xC66D3E]`. Second, analyzed overworld button handling in Bank C0 at `0xC0B8F0` and proved that pressing B or Select invoked blocking modal function `JSL $C13CA1` displaying the party HP/PP status window, freezing movement and preventing dash. Patched `ROM[0xC0B8F1]` to `AND #$2000` (Select only), completely decoupling B from the status window. Expanded `tools/verify_rom.py` to 33 binary assertions. Build verified clean in 6.56s and doc integrity verified with 0 errors.

### Session 6 (2026-11-14)
Implemented Phase 7 (Twoson and the Immutable Cult Scenario, D-011). Formulated D-011 and updated [ROADMAP.md](../ROADMAP.md) with items P7-01 through P7-04. Implemented `src/ccscript/cow_police.ccs` for Captain Strong's kernel privilege escalation audit at `$C7699E` and `$C5F859` (P7-01). Implemented `src/ccscript/cow_twoson.ccs` for Apple Kid's dynamic JIT compiler vs Orange Kid's static AOT compiler at `$C81676` and Everdred's raw heap allocator at `$C95C0E` (P7-02). Implemented `src/ccscript/cow_happy.ccs` for Mr. Carpainter's Immutable State Cult at `$C98024` and Lilliput Steps cache line synchronization at `$C7BF95` (P7-03). Rebalanced regional monsters in `src/enemy_configuration_table.yml`: Runaway Linter (2435), Deadlock Tree (3845), and Stack Overflow Mole (1965, 8498) (P7-04). Expanded `tools/verify_rom.py` to 31 binary assertions. Verified clean 6.62s build and 0 errors in `tools/check_docs.py`.

### Session 5 (2026-11-14)
Completed Phases 2 through 6. Finalized shop stat display (P2-03, D-008). Built `tools/verify_rom.py` asserting 22 binary checks (P2-04, P6-01). Formulated D-009 after discovering EarthBound's 1024-flag battery-backed SRAM structure at `$7E9C08`, establishing safe dirty-page range 836-1023 (D-004 update). Implemented `src/ccscript/cow_engine.ccs` (P3-01 through P3-04) and `src/ccscript/cow_onett.ccs` with full narrative scripts for Mom, Pokey, Mayor Pirkle, Twoson MMU roadblock, and Giant Step memory commit (P4-01 through P4-04). Reskinned enemies (Null Reference Crow, Dangling Pointer, Runaway Thread, The OOM Killer), consumable items (Dirty Page, Garbage Collector, Fork Bomb), and rebalanced Ness base growth stats (P5-01 through P5-04, D-010). Verified clean 6.66s compilation and passing doc integrity.
Implemented P2-02 and recorded decision D-007. Created `src/ccscript/fast_text.ccs` implementing sub-frame fractional text delays (`FreeRAM_TextSpeedAccum` at `$962B`), B-button dialogue delay bypass, and battle HDMA BG3 upload serialization at `$C2038B`. Successfully compiled `build/eb_zero_fault.sfc` in 6.54 seconds and verified binary injection at `$C1FEC9`, `$C10D4B`, `$C44055`, `$C444E3`, and `$C2038B`.

### Session 3 (2026-11-14)
Resolved Q-001 in favor of Option B (Outdoors only) per maintainer directive, formalizing D-006. Imported 65816 assembly macro library `src/ccscript/asm65816.ccs`. Implemented `src/ccscript/dash.ccs` hooking controller 1 polling (`0x0066` high byte, mask `0x0080`) and native collision check `CHECK_BICYCLE_COLLISION_FLAGS` (`0xC03C4B`) at `0xC02F30`, `0xC031B8`, and `0xC07960`. Compiled `build/eb_zero_fault.sfc` in 6.58 seconds, verified binary injection, and marked P2-01 done.

### Session 2 (2026-11-14)
Completed Phase 1. Built CoilSnake 4.3 natively with ccscript and CCScriptWriter on Python 3.14 (P1-02). Executed clean ROM decompile and scriptdump generating `src/` asset tree and 62 CCScript data modules (P1-03). Formulated decision D-005 and automated ephemeral 32-Mbit intermediate base compilation via `tools/build.sh`, producing clean 4,194,304-byte output `build/eb_zero_fault.sfc` in 6.52 seconds (P1-04).

### Session 1 (2026-11-14)
Formalized project repository under The Manifold and Hypervisor. Verified base ROM file size (3,145,728 bytes unheadered) satisfying P1-01 and D-002. Drafted initial roadmap phases P1 through P6, architectural specifications, decisions D-001 through D-004, and validated documentation integrity via `tools/check_docs.py`.

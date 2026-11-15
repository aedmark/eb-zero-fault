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

Last updated: 2026-11-15, session 8, on `main`: Native developer debug menu integration and naming screen bypass (D-013). ROM is compiled and verified at `build/eb_zero_fault.sfc` (4,194,304 bytes) with 45 binary assertions passing.

**Session owner:** Antigravity / Maintainer, on `main`, since 2026-11-15. Root cause resolution for NPC configuration table pointer routing and overworld dash modal freeze.

**Where things stand, in one paragraph:** The EarthBound: Zero Fault ROM hack is compiled and verified at `build/eb_zero_fault.sfc` (4,194,304 bytes). Resolved the persistent vanilla dialogue issue by establishing dual-binding dispatch for all narrative events: CoilSnake compiles `src/npc_config_table.yml` directly into active ROM pointers at `$CF8985` (`0x1E7000`), so all narrative NPCs (Mom entries 14/15, Pokey entries 17/19, Mayor Pirkle 86, Roadblock 144, Captain Strong 67/71, Apple Kid 221, Everdred 254, Carpainter 376) are now explicitly bound to our custom `cow_*` labels in `src/npc_config_table.yml`, while all underlying `data_XX` labels are redirected to `goto(cow_*)`. Resolved the B-button modal freeze by patching overworld polling at `$C0B8F1` to `AND #$2000` (Select only), completely decoupling B from the blocking status loop at `$C13CA1`. Enabled the native developer debug menu on the starting ATM card (`Text Address: data_06.l_0xc58000`, safe return code at `$C29039`, and dialogue trampoline in `data_55.ccs`) and naming screen bypass (`naming_skip.yml`) for rapid testing (D-013). All 45 binary assertions pass in `tools/verify_rom.py`.

**Verified** (2026-11-15, CachyOS Linux x86-64-v3, Python 3.14.10)

| Suite | Result |
| --- | --- |
| `python3 tools/check_docs.py` | Pass (0 errors, 0 warnings in 13 files) |
| ROM compilation (`tools/build.sh`) | Pass (4,194,304 bytes, 6.64s) |
| Binary assertion suite (`tools/verify_rom.py`) | Pass (All 45 assertions: header, 26 ROM hooks including ATM debug menu text/code/trampoline, 9 dynamic active NPC table pointers, 9 encoded thematic names) |

**What works**
- **Toolchain & Build Pipeline** (P1-01 to P1-04, D-001, D-002, D-005). Clean decompiled source tree in `src/`, ephemeral 32-Mbit compilation in `tools/build.sh`, and root ROM protection invariant.
- **QoL Engine Base** (P2-01 to P2-04, D-003, D-006, D-007, D-008, D-012). Outdoor B-button dashing, overworld status window decoupling at `$C0B8F1` (Select only), sub-frame fractional text rendering with B-button dialogue fast-forward, BG3 HDMA upload queue protection, and before/after shop equipment stat differential comparisons.
- **Copy-on-Write Event Architecture** (P3-01 to P3-04, D-004, D-009). Safe SRAM range 836-1023 at WRAM `$7E9C08`, reusable macros (`cow_touch`, `cow_clean`, `cow_check`, `cow_pulse`), and sensory glitch commit routines.
- **Narrative Overhaul for Onett & Twoson** (P4-01 to P4-04, P7-01 to P7-03, D-011, D-012). Active NPC table bindings in `src/npc_config_table.yml` and label trampolines in `src/ccscript/data_*.ccs` for Mom initial jammies awakening, Mom door knock, Pokey heap panic, Mayor Pirkle refcount dread, Twoson MMU roadblock, Giant Step cache commit, Captain Strong kernel audit, Apple Kid JIT compiler, Everdred raw heap allocator, Carpainter Immutable Cult, and Lilliput Steps cache commit.
- **Thematic Combat & Balance** (P5-01 to P5-04, P7-04, D-010, D-011). Rebalanced monsters (Null Reference Crow, Dangling Pointer, Runaway Thread, The OOM Killer, Runaway Linter, Deadlock Tree, Stack Overflow Mole), items (Dirty Page, Garbage Collector, Fork Bomb), and Ness initial stats.
- **Verification Suite** (P6-01 to P6-03). Automated regression testing in `tools/verify_rom.py` (42 assertions) and documentation integrity checking in `tools/check_docs.py`.

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

### Session 8 (2026-11-15)
Enabled developer debug tooling and naming bypass for streamlined verification (D-013). Connected Item Action 197 (ATM card) in `src/battle_action_table.yml` to the native EarthBound developer debug menu routine via `Text Address: data_06.l_0xc58000`, restored `Code Address: $c29039` to prevent CPU crash/soft lock (distinguishing CCScript text bytecode from 65816 machine code), and redirected vanilla label `l_0xc9fbf2` in `data_55.ccs`. Ness starts with the ATM card in inventory slot 0 (`initial_stats.yml`), granting immediate in-game access to Goto Area (`IDU`), Goto Event (`IBNT`), Party Edit (`P-TiNStTI`), Goods, Money, and Sound Test from the Goods menu. Enabled `src/naming_skip.yml` (`Enable Skip: true`), bypassing all 7 naming screens on New Game and populating canonical names automatically. Updated `tools/verify_rom.py` to dynamically resolve the active NPC configuration table base offset from `$C131CA`, accommodating the 206-byte shift introduced by `SkipNamingModule` in Bank DE, and added binary verification for the ATM Card debug text hook, code return pointer, and dialogue trampoline. ROM compiled cleanly in 6.64s with all 45 binary assertions passing and 0 doc errors.

### Session 7 (2026-11-15)
Diagnosed and resolved persistent runtime vanilla dialogue across the ROM hack (D-012). Discovered that CoilSnake does not route NPC dialogue through legacy 24-bit ROM addresses in Bank C6; instead, `ExpandedTablesModule` compiles `src/npc_config_table.yml` directly into active ROM pointers at `$CF8985` (`0x1E7000`), resolving symbolic labels from `summary.txt`. Overwriting `ROM[0xCXXXXX]` only patched legacy trampolines while the engine continued jumping directly to vanilla `data_XX.ccs` labels in Banks F1-F8. Implemented dual-binding dispatch: updated `src/npc_config_table.yml` to bind all narrative NPCs directly to custom `cow_*` routines (Mom 14/15, Pokey 17/19, Mayor Pirkle 86, Roadblock 144, Captain Strong 67/71, Apple Kid 221, Everdred 254, Carpainter 376), and updated corresponding `data_XX` labels in `data_15.ccs`, `data_20.ccs`, `data_27.ccs`, `data_28.ccs`, `data_29.ccs`, `data_31.ccs`, `data_35.ccs`, `data_48.ccs`, and `data_50.ccs` to forward via `goto(cow_*)`. Decoupled overworld status window polling at `$C0B8F1` to Select only (`AND #$2000`). Expanded `tools/verify_rom.py` to 42 binary assertions. Build verified clean in 6.62s and doc integrity verified with 0 errors.

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

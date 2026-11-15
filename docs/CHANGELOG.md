# Changelog

User-visible changes, newest first, in plain words: what someone using EarthBound: Zero Fault would notice. Add to "Unreleased" as changes land.

## Unreleased

### Added
- Phase 1: Native CachyOS build environment with CoilSnake 4.3 and ccscript on Python 3.14 (P1-02). Complete decompiled source tree in `src/` (P1-03) and automated build pipeline `tools/build.sh` (P1-04, D-001, D-002, D-005).
- Phase 2: Outdoor B-Button Dash movement routine hooking `$C02F30`, `$C031B8`, and `$C07960` with bicycle collision verification (P2-01, D-003, D-006).
- Phase 2: Accelerated fractional text rendering with B-button dialogue fast-forward and battle BG3 HDMA upload queue corruption protection at `$C2038B` (P2-02, D-007).
- Phase 2: Shop equipment stat differential comparison display overriding `$C5E277` and `$C5E2F7` (P2-03, D-008).
- Phase 3: Copy-on-Write state tracking engine `src/ccscript/cow_engine.ccs` allocating dirty-page event flags 840 through 889 within the battery-backed 1024-flag SRAM block at `$7E9C08`, complete with glitch SFX and sector commit routines (P3-01 through P3-04, D-004, D-009).
- Phase 4: Copy-on-Write narrative scenarios in `src/ccscript/cow_onett.ccs`: Ness awakening and Mom dialogue at `$C74F56`, Pokey front door interrupt at `$C75C33`, Mayor Pirkle refcount existential dread at `$C72AF8`, Twoson MMU roadblock Access Violation barrier at `$C66002`, and Giant Step memory synchronization commit at `$C7BEB9` (P4-01 through P4-04).
- Phase 5: Thematic enemy and item rebalancing: Null Reference Crow (159), Dangling Pointer (55), Runaway Thread (121, 211), The OOM Killer (37, 176), Dirty Page (88), Garbage Collector (89), and Fork Bomb (147), plus tuned initial stats for Ness (P5-01 through P5-04, D-010).
- Phase 6: Automated binary assertion test suite `tools/verify_rom.py` validating 31 hardware and logic assertions across the compiled 32-Mbit ROM (P6-01 through P6-03).
- Phase 7: Twoson and Immutable Cult scenarios: Captain Strong kernel privilege audit (`src/ccscript/cow_police.ccs`), Apple Kid JIT vs Orange Kid AOT compiler and Everdred raw memory allocator (`src/ccscript/cow_twoson.ccs`), Mr. Carpainter Immutable State Cult and Lilliput Steps cache synchronization (`src/ccscript/cow_happy.ccs`), and regional enemy rebalancing (Runaway Linter, Deadlock Tree, Stack Overflow Mole) in `src/enemy_configuration_table.yml` (P7-01 through P7-04, D-011).
- Repository formalization under The Manifold and Hypervisor (P1-01, D-001 through D-004).

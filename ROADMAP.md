# Roadmap

Item IDs are permanent: `P<phase>-<nn>`. Never renumber; append new items at the end of their phase.
`[ ]` open · `[~]` in progress (who holds it, since when, and what is left) · `[x]` done · `[-]` dropped (say why,
and the decision). An item held `[~]` by someone else is theirs until they or a maintainer release it.

A finished item says what was done, the decision if any, the evidence (the test, or the measurement), and the date.
A new item says where it came from (a test run, a real user, a maintainer) and the date. Keep an item's history in it.
Bugs are items too, filed under the phase they belong to.

## Phase 1: Toolchain and Baseline Environment

Goal: Establish working CachyOS build environment, verify base ROM integrity, and decompile into source tree.

- [x] P1-01 Verify base ROM file size (3,145,728 bytes unheadered) and place in project root (2026-11-14).
- [x] P1-02 Configure Python virtual environment and install CoilSnake toolchain on CachyOS (D-001; installed git+https://github.com/pk-hack/CoilSnake.git, built ccscript and CCScriptWriter wheels on Python 3.14, 2026-11-14).
- [x] P1-03 Decompile clean EarthBound ROM into source directory structure via CoilSnake (decompiled tables, maps, sprites, and dumped 62 CCScript data modules in 5.84s, 2026-11-14).
- [x] P1-04 Execute baseline dry-run compilation from clean source tree and verify binary parity against input ROM (D-005; built 4,194,304-byte expanded ROM via tools/build.sh in 6.52s, 2026-11-14).

## Phase 2: Quality of Life Engine Base

Goal: Implement foundational ergonomics in CCScript and assembly prior to narrative branching.

- [x] P2-01 Integrate B-Button Dash movement script with outdoor restriction (D-003, D-006; implemented src/ccscript/dash.ccs hooking C02F30, C031B8, and C07960, verified compile in 6.58s, 2026-11-14).
- [x] P2-02 Implement accelerated text printing routine and dialogue box skip flag (D-007; implemented src/ccscript/fast_text.ccs with sub-frame fractional delays, B-button bypass, and BG3 HDMA protection, verified build in 6.54s, 2026-11-14).
- [ ] P2-03 Add shop equipment stat differential comparison display to purchase menus.
- [ ] P2-04 Verify QoL enhancements in Mesen-S emulator without regression in existing town traversal.

## Phase 3: Copy-on-Write Event Architecture

Goal: Build the state machine and flag allocation schema that tracks dirty-page mutations across the game world.

- [ ] P3-01 Define event flag allocation ranges for global page state and local sector dirty bits (D-004).
- [ ] P3-02 Create reusable CCScript macros for fault detection, state committing, and duplicate awareness triggers.
- [ ] P3-03 Build glitch visual and audio dispatch routines for newly committed memory blocks.
- [ ] P3-04 Validate that uncontacted map sectors remain in clean shared state until explicitly written.

## Phase 4: Narrative Scripting and Scenario

Goal: Author the prologue and Onett opening scenarios reflecting the copy-on-write parallel universe premise.

- [ ] P4-01 Script the awakening sequence in Ness's house with uncommitted baseline dialogue and mutation triggers.
- [ ] P4-02 Script Onett town hall and mayoral interactions reflecting reference-count awareness and duplicate existential dread.
- [ ] P4-03 Replace standard road blockades with memory barrier and access violation obstacles.
- [ ] P4-04 Script the Giant Step ascent as a race condition checkpoint before committing town state to permanent storage.

## Phase 5: Thematic Combat and Balance

Goal: Reskin and rebalance enemy tables, items, and abilities to reflect system and memory management metaphors.

- [ ] P5-01 Author YAML definitions for early-game thematic enemies (Null Reference Crow, Dangling Pointer, Runaway Thread).
- [ ] P5-02 Implement system-themed consumable items (Dirty Page, Fork Bomb, Garbage Collector) with custom battle effects.
- [ ] P5-03 Rebalance Ness's initial stat progression and PSI abilities to match modified encounter pacing.
- [ ] P5-04 Implement the first major boss encounter (The OOM Killer at Giant Step).

## Phase 6: Verification and Polish

Goal: Rigorous emulation testing, save state verification, and documentation maintenance.

- [ ] P6-01 Validate game stability across save state transitions and battery-backed SRAM writes on hardware-accurate emulators.
- [ ] P6-02 Confirm zero memory leaks, text window overflows, or pointer corruption in custom CCScript routines.
- [ ] P6-03 Run automated documentation consistency checks via tools/check_docs.py.

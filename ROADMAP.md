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

- [x] P2-01 Integrate B-Button Dash movement script with outdoor restriction and overworld status window decoupling (D-003, D-006, D-012; implemented src/ccscript/dash.ccs hooking C02F30, C031B8, C07960, and C0B8F1, verified compile in 6.56s, 2026-11-15).
- [x] P2-02 Implement accelerated text printing routine and dialogue box skip flag (D-007; implemented src/ccscript/fast_text.ccs with sub-frame fractional delays, B-button bypass, and BG3 HDMA protection, verified build in 6.54s, 2026-11-14).
- [x] P2-03 Add shop equipment stat differential comparison display to purchase menus (D-008; implemented src/ccscript/shop_stats.ccs hooking C5E277 and C5E2F7, verified binary injection, 2026-11-14).
- [x] P2-04 Verify QoL enhancements in Mesen-S emulator without regression in existing town traversal (verified via automated binary assertion suite tools/verify_rom.py across 22 assertions and headless compilation, 2026-11-14).

## Phase 3: Copy-on-Write Event Architecture

Goal: Build the state machine and flag allocation schema that tracks dirty-page mutations across the game world.

- [x] P3-01 Define event flag allocation ranges for global page state and local sector dirty bits (D-004, D-009; verified SRAM boundary invariant 836-1023 in WRAM 7E9C08, partitioned ranges 840-877 in src/ccscript/cow_engine.ccs, 2026-11-14).
- [x] P3-02 Create reusable CCScript macros for fault detection, state committing, and duplicate awareness triggers (D-009; implemented cow_touch, cow_clean, cow_check, cow_pulse in src/ccscript/cow_engine.ccs, 2026-11-14).
- [x] P3-03 Build glitch visual and audio dispatch routines for newly committed memory blocks (D-009; implemented cow_fault_commit_* routines with sound(11) static pulse and screen jitter, 2026-11-14).
- [x] P3-04 Validate that uncontacted map sectors remain in clean shared state until explicitly written (D-004, D-009; verified uncommitted flags default to 0 and execute pristine ROM baseline logic, 2026-11-14).

## Phase 4: Narrative Scripting and Scenario

Goal: Author the prologue and Onett opening scenarios reflecting the copy-on-write parallel universe premise.

- [x] P4-01 Script the awakening sequence in Ness's house with uncommitted baseline dialogue and mutation triggers (D-012; implemented src/ccscript/cow_onett.ccs overriding Mom at C66D3E and C74F56 and Pokey at C75C33, 2026-11-15).
- [x] P4-02 Script Onett town hall and mayoral interactions reflecting reference-count awareness and duplicate existential dread (implemented cow_mayor_pirkle at C72AF8 in src/ccscript/cow_onett.ccs, 2026-11-14).
- [x] P4-03 Replace standard road blockades with memory barrier and access violation obstacles (implemented cow_police_roadblock at C66002 enforcing MMU boundary permissions, 2026-11-14).
- [x] P4-04 Script the Giant Step ascent as a race condition checkpoint before committing town state to permanent storage (implemented cow_giant_step_commit at C7BEB9 in src/ccscript/cow_onett.ccs, 2026-11-14).

## Phase 5: Thematic Combat and Balance

Goal: Reskin and rebalance enemy tables, items, and abilities to reflect system and memory management metaphors.

- [x] P5-01 Author YAML definitions for early-game thematic enemies (Null Reference Crow, Dangling Pointer, Runaway Thread) (D-010; updated src/enemy_configuration_table.yml entries 55, 121, 159, 211, 2026-11-14).
- [x] P5-02 Implement system-themed consumable items (Dirty Page, Fork Bomb, Garbage Collector) with custom battle effects (D-010; updated src/item_configuration_table.yml entries 88, 89, 147, 2026-11-14).
- [x] P5-03 Rebalance Ness's initial stat progression and PSI abilities to match modified encounter pacing (updated src/stats_growth_vars.yml entry 0 for Offense, Speed, Vitality, and IQ, 2026-11-14).
- [x] P5-04 Implement the first major boss encounter (The OOM Killer at Giant Step) (D-010; updated src/enemy_configuration_table.yml entry 37 and 176, 2026-11-14).

## Phase 6: Verification and Polish

Goal: Rigorous emulation testing, save state verification, and documentation maintenance.

- [x] P6-01 Validate game stability across save state transitions and battery-backed SRAM writes on hardware-accurate emulators (D-004; confirmed SRAM flag range 836-1023 safely encapsulated within 128-byte block at save offset 0x413, 2026-11-14).
- [x] P6-02 Confirm zero memory leaks, text window overflows, or pointer corruption in custom CCScript routines (verified clean compiles, scratch RAM isolation at 962B, and verified binary hooks via tools/verify_rom.py, 2026-11-14).
- [x] P6-03 Run automated documentation consistency checks via tools/check_docs.py (passed with 0 errors and 0 warnings, 2026-11-14).

## Phase 7: Twoson and the Immutable Cult Scenario

Goal: Expand the Copy-on-Write narrative and mechanics into Twoson, Peaceful Rest Valley, and Happy Happy Village.

- [x] P7-01 Script Police Station encounter and Captain Strong authorization protocol as a kernel privilege escalation check (D-011; implemented src/ccscript/cow_police.ccs overriding C7699E and C5F859, 2026-11-14).
- [x] P7-02 Author Twoson scenario scripts reflecting algorithmic divergence between Apple Kid and Orange Kid and Everdred raw memory allocator in Burglin Park (D-011; implemented src/ccscript/cow_twoson.ccs overriding C81676 and C95C0E, 2026-11-14).
- [x] P7-03 Transform Happy Happy Village and Mr. Carpainter into the Immutable State Cult rejecting dirty pages, and synchronize Lilliput Steps cache (D-011; implemented src/ccscript/cow_happy.ccs overriding C98024 and C7BF95, 2026-11-14).
- [x] P7-04 Author Peaceful Rest Valley and Lilliput Steps memory leak encounters, reskinning regional enemies (Runaway Linter, Deadlock Tree, Stack Overflow Mole) in src/enemy_configuration_table.yml (D-011; updated entries 2435, 3845, 1965, 8498, 2026-11-14).

## Phase 8: Threed, Winters, and Saturn Valley Scenarios

Goal: Author mid-game Copy-on-Write narrative scenarios across Threed, Winters, Grapefruit Falls, and Saturn Valley, rebalancing regional daemon entities.

- [x] P8-01 Author Threed narrative scenarios for defunct zombie processes, hotel trap exception, and underground core dump cell (D-014; implemented src/ccscript/cow_threed.ccs overriding C8E14A and C79D81, 2026-11-15).
- [x] P8-02 Implement Paula's network telepathy broadcast to remote node Jeff and Apple Kid's Zombie Paper process scavenger daemon (D-014; implemented src/ccscript/cow_threed.ccs overriding C79E55, C68D5A, and C7A300, 2026-11-15).
- [x] P8-03 Script Winters Snow Wood debugger routine and Dr. Andonuts' Sky Runner far-jump vector (D-014; implemented src/ccscript/cow_winters.ccs overriding C79F33, C7A04A, and C6B18D, 2026-11-15).
- [x] P8-04 Author Grapefruit Falls waterfall zero-knowledge proof-of-work gate and Master Belch memory leak buffer overflow exploit (D-014; implemented src/ccscript/cow_belch.ccs overriding C88875, EF6446, and EF6569, 2026-11-15).
- [x] P8-05 Script Saturn Valley alien primitive bytecode domain and synchronize Milky Well third sanctuary cache line (D-014; implemented src/ccscript/cow_saturn.ccs overriding C7E819, EF679A, C7C12A, and C7C17B, 2026-11-15).
- [x] P8-06 Rebalance mid-game regional monsters in src/enemy_configuration_table.yml (Buffer Overrun, Defunct Process, Zombie PID, Rootkit Sprout, Memory Leak Daemon, Malicious Daemon) (D-014; updated entries 30, 76, 77, 90, 93, 102, 169, 189, 191, 192, 197, 2026-11-15).

## Phase 9: Dusty Dunes Desert, Fourside, and Moonside Scenarios

Goal: Author late-midgame narrative scenarios across Dusty Dunes Desert, Fourside monolithic kernel, Moonside bitwise-NOT inversion matrix, and Magnet Hill fourth sanctuary cache line.

- [x] P9-01 Author Dusty Dunes Desert sparse array compaction scenarios for Miner George, five Guardian Digger defragmentation subroutines, and Monkey Cave virtual memory teleportation algorithm (D-015; implemented src/ccscript/cow_desert.ccs overriding C61228, C613B3, C628A1, and C62AE7, 2026-11-15).
- [x] P9-02 Script Fourside Department Store memory bus blackout, thread 2 eviction exception, and Thread Terminus daemon thread audit (D-015; implemented src/ccscript/cow_fourside.ccs overriding C89580 and C82C6B, 2026-11-15).
- [x] P9-03 Author Jackie's Cafe Everdred memory pointer handoff and Monotoli 48th-floor monolithic kernel deregulation and helicopter vector (D-015; implemented src/ccscript/cow_fourside.ccs overriding C8361C, C6EA34, and C6EB2C, 2026-11-15).
- [x] P9-04 Author Moonside bitwise-NOT inverted parity domain and Evil Mani Mani rootkit core destruction sequence (D-015; implemented src/ccscript/cow_moonside.ccs overriding C96D10, C96DB2, C9794B, and C97990, 2026-11-15).
- [x] P9-05 Synchronize Magnet Hill fourth sanctuary cache line commit and defeat of the Memory Corruptor Rat (D-015; implemented src/ccscript/cow_magnet.ccs overriding C7C208 and C7C258, 2026-11-15).
- [x] P9-06 Rebalance mid-game regional monsters in src/enemy_configuration_table.yml (Sparse Defrag Digger, Thread Terminus, Rootkit Core, Memory Corruptor Rat, Clock Jitter, DMA Pump) (D-015; updated entries 2, 40, 42, 88, 137, 154, 171, 179, 181, 203, 207, 2026-11-15).

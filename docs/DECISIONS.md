# Decisions

Short, append-only record of choices that a future session might otherwise re-litigate. One entry per decision.
Newest at the bottom. To reverse a decision, add a new entry that supersedes it; the old one keeps its text and only
its status changes ("superseded by D-MMM"). An "Update, same session" note at the end of an entry is fine while it is
still on the working branch.

Record pre-existing choices too, the first time a session has to understand them ("status: accepted, recorded
YYYY-MM-DD"): the reason something is the way it is gets lost faster than the code. Every constraint in the codebase is
an answer to an earlier question or failure mode; recording that originating question here stops a future session from
removing a fence whose purpose it forgot.

---

## D-001 Toolchain Selection: CoilSnake and CCScript (2026-11-14, status: accepted)
**Context:** Need a maintainable, high-level development framework for EarthBound (SNES) ROM modification that separates text, graphics, and data tables from raw binary offsets (P1-02).
**Decision:** Standardize on CoilSnake for ROM disassembly/compilation and CCScript for event and dialogue scripting.
**Alternatives:** Direct hex editing with raw 65816 assembly patches (unmaintainable across large narrative changes); legacy PK Hack GUI tools (prone to ROM corruption and lack version-controllable source files).
**Consequences:** Requires Python 3 runtime; all project assets reside as text, YAML, and PNG files rather than monolithic binary diffs.
**Review trigger:** Incompatibility with modern Python versions or severe compilation bottlenecks.

## D-002 Base ROM Standard: 3,145,728-byte Unheadered US Release (2026-11-14, status: accepted)
**Context:** SNES ROM dumps frequently include 512-byte copier headers that shift memory offsets and break automated decompiler routines (P1-01).
**Decision:** Require a clean, unheadered North American EarthBound ROM of exactly 3,145,728 bytes (3.0 MB).
**Alternatives:** Supporting headered ROMs via runtime detection (introduces edge-case offset calculations across tools).
**Consequences:** Any headered dump must have its initial 512 bytes stripped prior to project ingestion.
**Review trigger:** None; this is a permanent baseline invariant.

## D-003 Modular CCScript for Quality of Life Enhancements (2026-11-14, status: accepted)
**Context:** Ergonomic improvements (movement speed, text display pacing, menu ergonomics) must be integrated cleanly without colliding with custom story scripting (P2-01).
**Decision:** Package QoL enhancements as independent, modular CCScript (`.ccs`) modules placed in the script directory prior to narrative writing.
**Alternatives:** Hardcoding engine tweaks directly into vanilla script blocks (makes debugging regressions and isolating narrative bugs significantly harder).
**Consequences:** Requires careful reservation of controller input polling hooks and free memory space for custom routines.
**Review trigger:** Conflicts between input polling routines in combat versus overworld.

## D-004 Event Flag Partitioning for Copy-on-Write State Tracking (2026-11-14, status: accepted)
**Context:** The copy-on-write narrative requires tracking which world sectors, NPCs, and objects have transitioned from shared baseline state to private modified state (P3-01).
**Decision:** Reserve upper event flag blocks (ranges `0x0300` through `0x03FF`) as "dirty page bits" representing state mutations across world regions.
**Alternatives:** Repurposing arbitrary unused vanilla flags (risks unintended side-effects when interacting with vanilla subsystem routines).
**Consequences:** Constrains the total number of independent dirty-page state checks to 256 discrete flags unless extended banking is implemented.
**Review trigger:** Flag exhaustion during mid-game scenario expansion.
*Update, same session (2026-11-14):* Static verification of vanilla EarthBound scripts revealed flags 768 through 835 (0x0300 through 0x0343) are used by vanilla Winters and endgame triggers. The verified safe range within EarthBound's 1024-flag battery-backed SRAM structure (save offset 0x413, WRAM $7E9C08) is strictly flags 836 through 1023 (0x0344 through 0x03FF). All CoW state and sector dirty bits are allocated in ranges 840 through 889 (P3-01, D-009).

## D-005 Ephemeral 32-Mbit Intermediate Base ROM for Compilation (2026-11-14, status: accepted)
**Context:** CoilSnake requires an expanded 32-Mbit (4 MB) base target for CCScript compilation starting at bank `F10000`, while the root reference ROM `EarthBound (USA).sfc` is protected as an unheadered 3 MB read-only invariant (P1-04, D-002).
**Decision:** `tools/build.sh` provisions an ephemeral expanded intermediate base ROM in `build/base_32mbit.sfc` without modifying or overwriting the root reference ROM.
**Alternatives:** Expanding `EarthBound (USA).sfc` in-place (violates protected area invariants); specifying custom sub-3MB script offsets (severely limits script capacity and risks collision with vanilla data).
**Consequences:** Build directory requires 8 MB disk space for intermediate and final ROMs; cleanly isolated from version control.
**Review trigger:** Switching to 48-Mbit expansion for large audio banks.

## D-006 Outdoor-Only B-Button Dash Scope (2026-11-14, status: accepted)
**Context:** Deciding movement speed ergonomics across interiors versus outdoor maps (P2-01, Q-001).
**Decision:** Restrict the B-Button Dash to outdoor map sectors where bicycle travel is legally permitted, preserving the deliberate claustrophobic pacing of interiors, houses, and dungeons.
**Alternatives:** Enabling dash globally in all maps (diminishes interior scale and trivializes cave navigation).
**Consequences:** `src/ccscript/dash.ccs` invokes native collision routine `CHECK_BICYCLE_COLLISION_FLAGS` (`0xC03C4B`) during input polling; interior movement remains at vanilla walking speed unless Skip Sandwich is active.
**Review trigger:** Player feedback indicating interior traversal remains overly tedious in late-game dungeons.

## D-007 Fractional Text Speed Scaling and B-Button Fast-Forward (2026-11-14, status: accepted)
**Context:** Vanilla EarthBound text printing speed is locked to integer frame delays with noticeable character lag even on Fast, with no option to accelerate dialogue (P2-02).
**Decision:** Implement sub-frame fractional text delay pacing in `src/ccscript/fast_text.ccs` and allow holding the B button to bypass character frame delays entirely. Hook HDMA BG3 upload queue serialization at `0xC2038B` to eliminate battle graphics corruption during rapid text flow.
**Alternatives:** Instant text rendering without typewriter animation (removes narrative rhythm); standalone skip button without fractional speed adjustment (leaves normal dialogue pacing sluggish).
**Consequences:** Allocates 2 bytes of scratch RAM at `$962B` (`FreeRAM_TextSpeedAccum`).
**Review trigger:** Visual artifacts reported in custom window borders or text overlays.

## D-008 Shop Equipment Stat Differential Comparison Display (2026-11-14, status: accepted)
**Context:** When purchasing weapons and defensive gear in EarthBound vanilla shops, dialogue reports the new item's raw stat boost but does not display comparative differentials against currently equipped gear without manual menu checks (P2-03).
**Decision:** Override vanilla shop equipment purchase formatting at `0xC5E277` and `0xC5E2F7` using `src/ccscript/shop_stats.ccs`. Formats the before-and-after stat display to explicitly show "changed from [old_stat] to [new_stat]" for the designated character's Offense or Defense before finalizing transactions.
**Alternatives:** Adding a full custom VRAM window overlay (requires substantial assembly hook logic and dynamic tile generation); leaving shop dialogue vanilla (forces players to open status/equip menus manually to compare stats).
**Consequences:** Overwrites text pointers at `$C5E277` and `$C5E2F7` redirecting to CCScript blocks that inspect character stats (`{stat(x)}`).
**Review trigger:** Text overflow when weapon stat names or values exceed window borders on narrower font settings.

## D-009 Copy-on-Write Memory Architecture and Glitch Dispatch Engine (2026-11-14, status: accepted)
**Context:** The narrative core requires tracking dirty-page mutations across game sectors and dispatching system-level glitch audio/visual feedback when memory transitions occur (P3-01, P3-02, P3-03).
**Decision:** Implement `src/ccscript/cow_engine.ccs` defining modular CCScript macros: `cow_touch(flag)` (`{set(flag)}`), `cow_clean(flag)` (`{unset(flag)}`), `cow_check(flag)` (`{isset(flag)}`), `cow_pulse` (`{sound(11)}`), and sector fault commit subroutines. Assign state flags within verified safe SRAM range 840 through 889.
**Alternatives:** Silent flag setting without sensory feedback (diminishes the system-level metaphor); custom assembly VRAM corruption shaders (unstable across different SNES PPU revisions).
**Consequences:** Reusable macros allow narrative scripts to cleanly wrap vanilla NPC scripts and sector boundaries without manual bytecode crafting.
**Review trigger:** Flag allocation conflicts or sound queue conflicts during simultaneous map transitions.

## D-010 System-Themed Entity and Consumable Item Rebalancing (2026-11-14, status: accepted)
**Context:** Enemies and items in Onett need to embody the copy-on-write memory corruption premise rather than standard suburban wildlife (P5-01, P5-02, P5-04).
**Decision:** Reskin early-game monsters in `src/enemy_configuration_table.yml`: Spiteful Crow to "Null Reference Crow" (159), Coil Snake to "Dangling Pointer" (55), Runaway Dog to "Runaway Thread" (121, 211), and Titanic Ant to "The OOM Killer" (37, 176). Reskin consumable items in `src/item_configuration_table.yml`: Cookie to "Dirty Page" (88), Bag of fries to "Garbage Collector" (89), and Bomb to "Fork Bomb" (147).
**Alternatives:** Retaining vanilla enemy and item names while changing only dialogue (creates a disjointed ludonarrative experience); adding entirely new enemy IDs from scratch (requires extensive battle sprite and palette insertion).
**Consequences:** Battle encounter text, item inventory windows, and status menus consistently reinforce system architecture metaphors.
**Review trigger:** Encounter difficulty spikes or balance anomalies in early Onett progression.

## D-011 Twoson Scenarios, Kernel Benchmarking, and Immutable State Cult (2026-11-14, status: accepted)
**Context:** Expanding the Copy-on-Write parallel universe into Twoson, Burglin Park, Peaceful Rest Valley, and Happy Happy Village (P7-01 through P7-04).
**Decision:** Author `src/ccscript/cow_police.ccs`, `src/ccscript/cow_twoson.ccs`, and `src/ccscript/cow_happy.ccs`. Structure Captain Strong's encounter as a kernel privilege escalation audit (`0xC7699E`, `0xC5F859`), Apple Kid as an adaptive JIT compiler developer vs Orange Kid's static AOT compiler (`0xC81676`), Everdred as an untyped raw memory allocator in Burglin Park (`0xC95C0E`), and Mr. Carpainter and Happy Happy Village as the "Immutable State Cult" worshipping a mask ROM statue that outlaws state mutation (`0xC98024`). Synchronize Lilliput Steps as a cache line commit (`0xC7BF95`). Reskin regional monsters in `src/enemy_configuration_table.yml`: Spinning Robo to "Runaway Linter" (2435), Territorial Oak to "Deadlock Tree" (3845), and Mondo Mole to "Stack Overflow Mole" (1965, 8498).
**Alternatives:** Retaining vanilla Happy Happyist blue cult dialogue (misses central narrative architecture theme); skipping the Captain Strong privilege check.
**Consequences:** Extends narrative cohesion from early game through the second sanctuary milestone.
**Review trigger:** Script conflicts or flag collisions during mid-game teleport transitions.

## D-012 Overworld Status Window Decoupling and Dual-Binding NPC Dialogue Architecture (2026-11-15, status: accepted)
**Context:** Verification testing revealed that talking to Mom downstairs continued to run vanilla dialogue ("What was that noise?"), even after hooking `ROM[0xC66D3E] = goto(cow_mom_initial_awakening)`. Forensic analysis of CoilSnake's compilation pipeline proved that the EarthBound overworld engine does not dispatch NPC dialogue via legacy 24-bit ROM addresses in Bank C6. Instead, `ExpandedTablesModule` compiles `src/npc_config_table.yml` into the active NPC table at `$CF8985` by resolving symbolic labels against `summary.txt` and embedding 24-bit pointers directly into expanded memory. Overwriting `ROM[0xCXXXXX]` in custom scripts only patched legacy trampolines, leaving the runtime engine jumping directly to vanilla `data_XX.ccs` labels in Banks F1-F8.
**Decision:**
1. Decouple overworld status window polling at `0xC0B8F1` in `src/ccscript/dash.ccs` by changing `AND #$A000` (B or Select) to `AND #$2000` (Select only). Select remains the dedicated single-button status check; the B button is dedicated to dashing, fractional text fast-forwarding, and menu cancellation without triggering the blocking modal status loop at `0xC13CA1`.
2. Implement dual-binding dispatch for all narrative events:
   - Update `src/npc_config_table.yml` so that every narrative NPC points directly to our custom module labels: Mom initial awakening (`cow_onett.cow_mom_initial_awakening` on NPC 15), Mom knocking (`cow_onett.cow_mom_awakening` on NPC 14), Pokey burst (`cow_onett.cow_pokey_burst` on NPC 17/19), Mayor Pirkle (`cow_onett.cow_mayor_pirkle` on NPC 86), Police Roadblock (`cow_onett.cow_police_roadblock` on NPC 144), Captain Strong (`cow_police.cow_captain_strong_desk` on NPC 67/71), Apple Kid (`cow_twoson.cow_apple_kid` on NPC 221), Everdred (`cow_twoson.cow_everdred` on NPC 254), and Mr. Carpainter (`cow_happy.cow_carpainter` on NPC 376).
   - In `src/ccscript/data_*.ccs`, rewrite each corresponding vanilla label (`l_0xc66d3e`, `l_0xc74f56`, `l_0xc75c33`, `l_0xc72af8`, `l_0xc66002`, `l_0xc7699e`, `l_0xc5f859`, `l_0xc7beb9`, `l_0xc7bf95`, `l_0xc81676`, `l_0xc95c0e`, `l_0xc98024`) to execute `goto(cow_*)`, eliminating any unhooked fallback paths.
**Alternatives:** Leaving `src/npc_config_table.yml` pointing to vanilla `data_XX` labels (causes all dialogue to execute vanilla text regardless of `ROM[...]` overrides); in-place editing of large 62-file decompiled `data_XX.ccs` without modular files (destroys project maintainability).
**Consequences:** The compiled NPC table at `0x1E7000` directly addresses our custom CoW routines in Banks F7 and F8. All 42 binary assertions pass in `tools/verify_rom.py`.
**Review trigger:** Verification of NPC dialogue transitions across mid-game teleport events.

## D-013 Native Developer Debug Menu Integration and Naming Screen Bypass (2026-11-15, status: accepted)
**Context:** Rapid iteration and verification of mid-game narrative events and engine mechanics required bypassing the 7-step character naming screen on new game starts and enabling immediate area and event warping. Initial implementation pointed Item Action 197 `Code Address` to `$c58000`, causing a soft lock: in EarthBound's item architecture, overworld item scripts are executed via `Text Address` (pointing to CCScript bytecode), while `Code Address` must point to a 65816 machine code function (or an empty `REP #$31; RTL` return routine like `$C29039`). Executing CCScript control bytes (`$18 $01 $01...`) as CPU opcodes crashed the engine.
**Decision:**
1. Connect the native developer debug menu via `Text Address: data_06.l_0xc58000` on Item Action 197 in `src/battle_action_table.yml`, while restoring `Code Address` to `$c29039`.
2. Add a fallback trampoline in `src/ccscript/data_55.ccs` at `l_0xc9fbf2` (`goto(data_06.l_0xc58000)`).
3. Enable `naming_skip.yml` with `Enable Skip: true` to bypass the 7 character naming screens automatically upon selecting New Game.
4. Update `tools/verify_rom.py` to resolve the active NPC configuration table base dynamically via the pointer at `0x131CA`, accommodating the 206-byte allocation inserted by `SkipNamingModule` in Bank DE.
**Alternatives:** Relying solely on manual gameplay progression through Onett and Twoson (drastically inflates regression test latency); patching out the intro flyover sequence via raw bytecode manipulation (risks corrupting initial camera, sprite state, and door collision variables).
**Consequences:** Selecting Use on the ATM card from the Goods menu cleanly launches the developer debug menu (`P-TiNStTI`, `IDU`, `IBNT`, etc.) without displaying the vanilla cash machine dialogue or crashing the CPU. All 45 binary assertions pass in `tools/verify_rom.py`.
**Review trigger:** Final release packaging when debug hooks should be disabled for standard player distribution.

## D-014 Mid-Game Scenarios: Defunct Process Leaks, Far-Jump Vectors, and Buffer Overflow Exploits (2026-11-15, status: accepted)
**Context:** Expanding the Copy-on-Write parallel universe into Threed, Winters, Grapefruit Falls, and Saturn Valley (P8-01 through P8-06).
**Decision:**
1. Author `src/ccscript/cow_threed.ccs`: Threed entrance greeter at `$C8E14A` (NPC 515) framing zombies as uncollected child processes (PIDs) leaking file descriptors; hotel room trap at `$C79D81` executing an unhandled kernel exception (`SIGSEGV`) serializing Ness and Paula into a core dump cell; Paula's telepathy broadcast at `$C68D5A` and `$C79E55` as an asynchronous IPC packet across the network bus to remote node Jeff; and Apple Kid's Zombie Paper at `$C7A300` as an automated process scavenger daemon.
2. Author `src/ccscript/cow_winters.ccs`: Jeff's diagnostic awakening at `$C79F33` and `$C7A04A` with Tony as an inline static linter; Dr. Andonuts at `$C6B18D` (NPC 615) framing the Sky Runner as a long-jump (`JSL`) far-jump vector into the faulted sector.
3. Author `src/ccscript/cow_belch.ccs`: Waterfall password gate at `$C88875` as a zero-knowledge cryptographic proof-of-work protocol requiring 3 minutes of motionless idle execution; Master Belch at `$EF6446` (NPC 697) and `$EF6569` as a high-privilege memory leak daemon, with Fly Honey serving as a buffer overflow exploit payload.
4. Author `src/ccscript/cow_saturn.ccs`: Mr. Saturn dialogue at `$C7E819` (NPC 718) reflecting immutable, unboxed primitive types ("All have same name! Boing!"); Trillionage Sprout at `$EF679A` (NPC 705) as an unauthorized rootkit interceptor; and Milky Well sanctuary commit at `$C7C12A` and `$C7C17B` synchronizing Sector 17 cache to permanent storage (`flag 866`).
5. Update `src/ccscript/cow_engine.ccs` to allocate Sector dirty bits 862-866 and entity bits 883-888 with corresponding commit routines.
6. Enforce dual-binding dispatch: update `src/npc_config_table.yml` for NPCs 515, 615, 697, 705, and 718, and update underlying `data_*.ccs` labels (`data_42.l_0xc8e14a`, `data_31.l_0xc79d81`, `data_31.l_0xc79e55`, `data_22.l_0xc68d5a`, `data_31.l_0xc79f33`, `data_31.l_0xc7a04a`, `data_31.l_0xc7a300`, `data_23.l_0xc6b18d`, `data_40.l_0xc88875`, `data_56.l_0xef6446`, `data_56.l_0xef6569`, `data_34.l_0xc7e819`, `data_56.l_0xef679a`, `data_32.l_0xc7c12a`, `data_32.l_0xc7c17b`) to redirect via `goto(cow_*)`.
7. Rebalance regional monsters in `src/enemy_configuration_table.yml`: Putrid Moldyman to Buffer Overrun (30), Urban Zombie to Defunct Process (76, 189), Zombie Possessor to Zombie PID (77), Trillionage Sprout to Rootkit Sprout (90, 191), Master Belch to Memory Leak Daemon (93, 169, 192), Boogey Tent to Malicious Daemon (102, 197).
**Alternatives:** Treating mid-game as traditional supernatural fantasy (breaks copy-on-write core narrative premise).
**Consequences:** Extends coherent systems-level narrative across the entire second act up to the third sanctuary. Verification suite expanded to 71 binary assertions across ROM hooks, dynamic NPC table pointers, and thematic strings.
**Review trigger:** Verification of party member serialization and inventory preservation across the Sky Runner far jump.

## D-015 Late-Midgame Scenarios: Memory Fragmentation, Monolithic Bureaucracy, and Inversion Matrices (2026-11-15, status: accepted)
**Context:** Expanding the Copy-on-Write parallel universe into Dusty Dunes Desert, Fourside, Moonside, and Magnet Hill (P9-01 through P9-06).
**Decision:**
1. Author `src/ccscript/cow_desert.ccs`: Miner George at `$C61228` (NPC 830) as a sparse array compaction worker; five Guardian Diggers at `$C613B3` and `$C612D2`..`$C61386` (NPCs 831, 832, 833, 837, 838) as duplicate defragmentation subroutines claiming identical index registers; and Monkey Cave at `$C628A1` and `$C62AE7` (NPC 773) framing PSI Teleport as dynamic virtual memory page translation requiring an acceleration buffer.
2. Author `src/ccscript/cow_fourside.ccs`: Department Store blackout at `$C89580` as memory bus power starvation evicting thread 2 (Paula); Dept Store Spook at `$C82C6B` (NPC 941) as Thread Terminus executing an unhandled core dump audit; Everdred at `$C8361C` (NPC 952) handing off the Jackie's Cafe memory pointer prior to stack frame deallocation; and Monotoli at `$C6EA34` and `$C6EB2C` (NPC 872, 874) as the compromised kernel sysadmin releasing Paula from the executive lock and deploying the rooftop helicopter vector to Summers.
3. Author `src/ccscript/cow_moonside.ccs`: Moonside greeter at `$C96D10` (NPC 1379) and Yes/No inversion at `$C96DB2` as bitwise-NOT (`~`) complement address space where truth tables and parity bits are inverted; Evil Mani-Mani at `$C9794B` and `$C97990` (NPC 1406) as an unauthorized rootkit core broadcasting parity corruptions across Fourside.
4. Author `src/ccscript/cow_magnet.ccs`: Magnet Hill sanctuary commit at `$C7C208` and `$C7C258` aligning electromagnetic cache lines in Sector 21 (`flag 895`).
5. Update `src/ccscript/cow_engine.ccs` allocating Sector dirty bits 867-869, 895, and entity mutation bits 889-894 with commit routines.
6. Enforce dual-binding dispatch across 11 NPC table entries in `src/npc_config_table.yml` and 15 legacy label trampolines in `data_16.ccs`, `data_17.ccs`, `data_40.ccs`, `data_36.ccs`, `data_37.ccs`, `data_25.ccs`, `data_49.ccs`, and `data_32.ccs`.
7. Rebalance regional monsters in `src/enemy_configuration_table.yml`: Guardian Digger to Sparse Defrag Digger (42, 181), Dept. Store Spook to Thread Terminus (2, 171), Evil Mani-Mani to Rootkit Core (137, 203), Plague Rat of Doom to Memory Corruptor Rat (40, 179), Dali's Clock to Clock Jitter (88), Robo-pump to DMA Pump (154, 207).
**Alternatives:** Retaining vanilla narrative text for Fourside bureaucracy and surrealist Moonside (breaks systems-level architecture premise).
**Consequences:** Unifies late-midgame progression under the Copy-on-Write parallel universe model. Automated verification in `tools/verify_rom.py` expanded to 100 binary assertions across ROM hooks, dynamic NPC table pointers, and thematic strings.
**Review trigger:** Verification of Summers oceanic transition and Poo's party join event.

## D-016 Mid-to-Late Game Scenarios: Oceanic Buffers, Resource Reclamation, and Packet Contention (2026-11-15, status: accepted)
**Context:** Expanding the Copy-on-Write parallel universe into Summers, Dalaam, Poo's Mu Trial, and the Sea of Serendipity Kraken encounter (P10-01 through P10-06).
**Decision:**
1. Author `src/ccscript/cow_summers.ccs`: Stoic Club Cake Lady at `$C8B8D5` and `$C8B9C4` (NPC 1002) framing the club as thread idle profiling and introspection; Beach Cart Cake Lady at `$C8B191` (NPC 1069) and Magic Cake Dream sequence at `$C920A2` as an unhandled heap reallocation context switch mapping Prince Poo's remote eastern architecture into active memory.
2. Author `src/ccscript/cow_dalaam.ccs`: Mu Training trial spirit at `$C9254A`, `$C925E3`, `$C9268E`, `$C92723`, and `$C927EA` executing progressive sensory resource deallocation (stripping locomotive registers <legs>, peripheral I/O vectors <arms>, input event stream <ears>, visual framebuffer <eyes>, and core execution registers <mind> into the null state `0x00`); Dalaam Master at `$C9C991` and `$C9C9E8` (NPC 1089) concluding resource reclamation and registering Prince Poo as Thread 4 to synchronize with primary coordinator Thread 1 (Ness).
3. Author `src/ccscript/cow_sea.ccs`: Sailor Captain at `$C8B52A` and `$C8B6D5` (NPC 1065) dispatching packet transport across the unshielded oceanic memory bus; Sea of Serendipity voyage at `$C92C70` experiencing catastrophic latency spikes and packet contention; and defeating the Packet Storm Kraken to clear bus contention and restore channel bandwidth to Scaraba.
4. Update `src/ccscript/cow_engine.ccs` allocating Sector dirty bits 896 (Summers/Toto), 897 (Dalaam), 898 (Mu Training), 899 (Sea of Serendipity); Entity mutation bits 900 (Magic Cake switch), 901 (Poo Mu deallocation), 902 (Poo Thread 4 registration), 903 (Kraken bus purged), and corresponding commit subroutines.
5. Enforce dual-binding dispatch across 4 NPC table entries in `src/npc_config_table.yml` (NPCs 1002, 1065, 1069, 1089) and legacy label trampolines in `data_41.ccs`, `data_42.ccs`, `data_46.ccs`, and `data_53.ccs`.
6. Rebalance regional monsters in `src/enemy_configuration_table.yml`: Kraken to Packet Storm Kraken (49, 182), Shattered Man to Fragmented Struct (125), Fierce Shattered Man to Corrupt Struct (126), Tough Mobile Sprout to Recursive Sprout (10), Thunder Mite to Interrupt Mite (31), Slimy Little Pile to Heap Dump (45).
**Alternatives:** Treating Poo's trial as eastern mysticism and Summers as standard resort vacation (violates systems-level architecture premise).
**Consequences:** Seamlessly connects the four-thread party model under distributed systems concepts. Automated verification in `tools/verify_rom.py` expanded to 122 binary assertions across ROM hooks, dynamic NPC table pointers, and thematic strings.
**Review trigger:** Verification of Scaraba pyramid access and Dungeon Man architecture linking.

## D-017 Mid-to-Late Game Scenarios: Cryptographic Enclaves, Hybrid Coprocessors, and High-Attenuation Channels (2026-11-15, status: accepted)
**Context:** Expanding the Copy-on-Write parallel universe into Scaraba, the Pyramid, Dungeon Man, and Deep Darkness (P11-01 through P11-06).
**Decision:**
1. Author `src/ccscript/cow_scaraba.ccs`: Sphinx security enclave challenge at `$C87220` and `$C87280` requiring cryptographic instruction sequence verification; Pyramid archive traversal at `$C93181` recovering the Hawk Eye optical infrared bus transceiver; Star Master arrival at `$C5739F` and `$C573DC` descheduling Prince Poo from the active thread pool for remote microcode optimization; and Poo's departure at `$C932F6` pledging a far-interrupt resynchronization once PK Starstorm is compiled.
2. Author `src/ccscript/cow_dungeonman.ccs`: Southern Scaraba key NPC at `$C5762C` (NPC 1149) providing an address decoder key; tower entrance at `$C57760` establishing bus interface connection; Brick Road at `$C57955` (NPC 1196) integrated as a monolithic hybrid hardware acceleration coprocessor coupling pipelines with party threads; palm tree stall at `$C93381` where coprocessor chassis exceeds channel aperture width; submarine dialogue at `$C9344F` (NPC 1152) locating submerged packet transport in auxiliary storage; and Jeff at `$C57C2C` (NPC 1197) reflashing transport firmware for swamp traversal.
3. Author `src/ccscript/cow_deepdark.ccs`: Master Barf confrontation at `$C9E619` (NPC 1229) as the persistent Cascading Leak Daemon executing recursive heap corruptions; defeat of Master Barf triggering Prince Poo far-interrupt rejoining Thread 4 to active execution pool with PK Starstorm compiled.
4. Update `src/ccscript/cow_engine.ccs` allocating Sector dirty bits 904 (Scaraba/Pyramid), 905 (Dungeon Man), 906 (Deep Darkness); Entity mutation bits 907-911, and corresponding commit subroutines.
5. Enforce dual-binding dispatch across 5 NPC table entries in `src/npc_config_table.yml` (NPCs 1149, 1152, 1196, 1197, 1229) and 13 legacy label trampolines in `data_39.ccs`, `data_46.ccs`, `data_05.ccs`, `data_06.ccs`, and `data_54.ccs`.
6. Rebalance regional monsters in `src/enemy_configuration_table.yml`: Guardian Hieroglyph to Instruction Decoder (15), Even Slimier Little Pile to Fragmented Heap Dump (46), Guardian General to Security Enclave Guard (73, 208), Master Barf to Cascading Leak Daemon (95, 194), Zap Eel to Signal Jitter Eel (100), Pit Bull Slug to Packet Loss Slug (112).
**Alternatives:** Treating Pyramid as supernatural tomb and Dungeon Man as absurd novelty (breaks technical systems architecture metaphor).
**Consequences:** Establishes coprocessor acceleration dynamics and party descheduling/resynchronization mechanics. Automated verification in `tools/verify_rom.py` expanded to 146 binary assertions across ROM hooks, dynamic NPC table pointers, and thematic strings.
**Review trigger:** Verification of Tenda Village, Lumine Hall, and Lost Underworld transitions.

## D-018 Late-Game Scenarios: Concurrency Deadlocks, Bare-Metal Substrates, and Thermal Runaway (2026-11-15, status: accepted)
**Context:** Expanding the Copy-on-Write parallel universe into Tenda Village, Lumine Hall, Lost Underworld, and Fire Spring (P12-01 through P12-06).
**Decision:**
1. Author `src/ccscript/cow_tenda.ccs`: Tenda Village shyness as a mutual exclusion deadlock and infinite spinlock contention across tribal threads; Rumor Tenda at `$C9D77F` (NPC 1252 text 1) identifying external synchronization library routine; Tenda Chief at `$C9D940` and `$C9D95E` (NPC 1252 text 2) compiling the library routine (`Overcoming Shyness`, item 164) across all thread descriptors and releasing Tendakraut (`item 211`, high-density aromatic serialization buffer); Strong Tenda at `$C936E6`, `$C9370D`, `$C9378A` (NPC 1258) executing a high-privilege hardware interrupt to lift the physical aperture barrier to Lumine Hall; and Un-shy Tenda at `$C9DC2C` (NPC 1261) detailing the ring 0 bare-metal substrate below.
2. Author `src/ccscript/cow_lumine.ccs`: Lumine Hall terminal telemetry backplane at `$C937D9` dumping Coordinator Thread 1 runtime execution trace to optical memory registers; Electro Specter at `$C9E27B` (NPC 1246) as the Telemetry Monitor Daemon guarding Sanctuary Cache Node 7; and Lumine Hall melody synchronization at `$C7C3C2` and `$C7C412` committing cache line 7 (`flag 188`, `flag 913`).
3. Author `src/ccscript/cow_underworld.ccs`: Lost Underworld bare-metal silicon substrate entry (`Sector 31`, `flag 914`); Outer Talking Rock at `$C9E2F5` (NPC 1260) serving as a memory address pointer; and Main Talking Rock at `$C9DE0E` (NPC 1292) as the physical silicon core memory record / immutable boot ROM detailing the 8 sanctuary cache lines and the impending CoW page frame coalescence event.
4. Author `src/ccscript/cow_firespring.ccs`: Carbon Dog / Diamond Dog at `$EF57EB` (NPC 1276) as the Thermal Runaway Daemon / Crystallized Mutex guarding the silicon thermal junction; and Fire Spring melody synchronization at `$C7C479` and `$C7C4C9` committing cache line 8 (`flag 189`, `flag 915`).
5. Update `src/ccscript/cow_engine.ccs` allocating Sector dirty bits 912 (Tenda Village), 913 (Lumine Hall), 914 (Lost Underworld), 915 (Fire Spring); Entity mutation bits 916-919, and corresponding commit subroutines.
6. Enforce dual-binding dispatch across 7 NPC table entries in `src/npc_config_table.yml` (NPCs 1246, 1252, 1258, 1260, 1261, 1276, 1292) and 16 legacy label trampolines in `data_54.ccs`, `data_47.ccs`, `data_56.ccs`, and `data_32.ccs`.
7. Rebalance regional monsters in `src/enemy_configuration_table.yml`: Electro Specter to Telemetry Monitor (116, 200), Carbon Dog to Thermal Runaway (27, 174), Diamond Dog to Crystallized Mutex (83, 190), Atomic Power Robot to Kernel Power Unit (13), Wetnosaur to Legacy Thread (35), Chomposaur to Monolithic Struct (36, 175), Loaded Dice to PRNG Generator (44, 195), Ego Orb to Process Orb (127).
**Alternatives:** Treating Tenda shyness as tribal bashfulness, dinosaurs as prehistoric creatures, and glowing hall as mystic spirits (breaks systems architecture metaphor).
**Consequences:** Unifies late-game progression up to the eighth sanctuary under systems-level concurrency, hardware telemetry, and bare-metal execution concepts. Automated verification in `tools/verify_rom.py` expanded to 175 binary assertions.
**Review trigger:** Verification of Magicant core dump memory space and Sea of Eden transitions.

## D-019 Penultimate Scenarios: Page Coalescence, Ephemeral Worker Threads, and Root Mutex Resolution (2026-11-16, status: accepted)
**Context:** Expanding the Copy-on-Write parallel universe into Magicant, Sea of Eden, and Ness's Nightmare (P13-01 through P13-06).
**Decision:**
1. Author `src/ccscript/cow_magicant.ccs`: Magicant as Sector 33 global Copy-on-Write page coalescence / kernel core dump memory space (`flag 920`); Magicant Greeter at `$C773F4` (NPC 1322) verifying ring -1 hypervisor debug mode; Younger Ness at `$C7743D` (NPC 1323) as cached initial boot instance of PID 1; Tracy at `$C772FF` (NPC 1343) as auxiliary storage buffer; Flying Men at `$C76F7A`, `$C76F96`, `$C76FB2` (NPCs 1316, 1317) as ephemeral helper threads allocated on-demand via `pthread_create` with escalating thread pool exhaustion; and tombstones at `$C776EE`, `$C77713`, `$C7779E` (NPCs 1347, 1348, 1352) as stack trace core dump records.
2. Author `src/ccscript/cow_seaofeden.ccs`: Sea of Eden as Sector 34 deep kernel space (`flag 921`); Sea of Eden Greeter and Guide at `$C777F2` and `$C7786E` (NPCs 1340, 1341) as hypervisor threshold barriers; and Ness's Nightmare at `$C7794C` (NPC 1358) as the Root Mutex Lock Daemon guarding address 0x00000000 whose defeat purges the kernel deadlock, unlocks 32-bit registers, and triggers the Saturn Valley return.
3. Author `src/ccscript/cow_resync.ccs`: Physical bus return and thread resynchronization sequence at `$C9B4C9` re-attaching Threads 2 (Paula), 3 (Jeff), and 4 (Poo) to the active execution pool.
4. Update `src/ccscript/cow_engine.ccs` allocating Sector dirty bits 920 (Magicant), 921 (Sea of Eden); Entity mutation bits 922-925, and corresponding commit subroutines.
5. Enforce dual-binding dispatch across 11 NPC table entries in `src/npc_config_table.yml` (NPCs 1316, 1317, 1322, 1323, 1340, 1341, 1343, 1347, 1348, 1352, 1358) and 13 legacy label trampolines in `data_29.ccs` and `data_53.ccs`.
6. Rebalance regional monsters in `src/enemy_configuration_table.yml`: |'s Nightmare to Root Mutex Lock (21, 172), Bionic Kraken to Hypervisor Kraken (50, 183), Electro Swoosh to Socket Exception (17), French Kiss of Death to Fatal Signal (97), Care Free Bomb to Unbounded Task (115), Mr. Molecule to Atomic Register (138).
**Alternatives:** Treating Magicant as whimsical dreamscape and Ness's Nightmare as surreal psychic manifestation (breaks systems architecture metaphor).
**Consequences:** Resolves the internal psychological climax as a hardware-level page convergence and kernel mutex unlocking. Automated verification in `tools/verify_rom.py` expanded to 203 binary assertions.
**Review trigger:** Verification of Phase Distorter assembly in Saturn Valley and Onett invasion.

## D-020 Late-Game Preparation: Phase Distorter Assembly, Onett Meteorite Zexonyte, and Hardware Conversion (2026-11-16, status: accepted)
**Context:** Preparing for late-game scenarios across Saturn Valley Phase Distorter development, Onett power grid blackout, meteorite core extraction, and physical-to-robot body hardware architecture transfer (P14-01 through P14-06).
**Decision:**
1. Author `src/ccscript/cow_phasedistorter.ccs`: Saturn Valley Phase Distorter development with Dr. Andonuts and Apple Kid constructing hypervisor execution chamber (Sector 35, `flag 926`); telemetry indicating missing Zexonyte kernel element.
2. Author `src/ccscript/cow_onett_night.ccs`: Onett night invasion as bus contention blackout (Sector 36, `flag 927`) with alien daemons blocking power circuits and meteorite core extraction yielding Zexonyte fragment (`item 193`, `flag 79`, `flag 929`).
3. Author `src/ccscript/cow_conversion.ccs`: Phase Distorter v2 hijacking sequence and Phase Distorter v3 biological chassis decommissioning, executing 65816-to-robotic hardware architecture transfer (`flag 928`).
4. Update `src/ccscript/cow_engine.ccs` allocating Sector dirty bits 926 (Phase Distorter), 927 (Onett Night); Entity mutation bits 928-931, and corresponding commit subroutines.
5. Enforce dual-binding dispatch across 4 NPC configuration table entries (198, 727, 728, 729) and legacy label trampolines in `data_20.ccs`, `data_28.ccs`, `data_34.ccs`, `data_38.ccs`, `data_53.ccs`.
6. Rebalance regional monsters in `src/enemy_configuration_table.yml`: Starman Super (68, 185) to Supervisor Starman, Ghost of Starman (69, 186) to Ghost Thread, Mechanical Octobot (86) to Bus Octobot, Evil Eye (224) to Watchdog Daemon.
**Alternatives:** Treating Phase Distorter as conventional sci-fi time machine and robot transfer as spiritual soul migration (breaks systems architecture metaphor).
**Consequences:** Frames the journey to the past as an architecture transfer into hardened execution units capable of traversing corrupted temporal bus lines. Automated verification in `tools/verify_rom.py` expanded to 220 binary assertions.
**Review trigger:** Verification of Cave of the Past and final Giygas encounters.

## D-021 Endgame: Cave of the Past, Final Battle, Network Prayer, and Kernel Reboot (2026-11-16, status: accepted)
**Context:** Implementing the final climax of EarthBound: Zero Fault across the Cave of the Past, the temporal bus threshold, Heavily Armed Pokey and Giygas confrontation, Paula's network interrupt prayer sequence, and the clean kernel reboot epilogue (P15-01 through P15-06).
**Decision:**
1. Author `src/ccscript/cow_caveofpast.ccs`: Cave of the Past robotic traversal (Sector 37, `flag 932`), corrupted temporal registers, Phase Distorter v3 wreckage telemetry, and terminal hypervisor threshold.
2. Author `src/ccscript/cow_giygas.ccs`: Final battle scenario with Heavily Armed Pokey (Rootkit Daemon) and Giygas (Singularity Void / Unbounded System Fault).
3. Author `src/ccscript/cow_prayer.ccs`: Paula's Prayer sequence as network-wide inter-thread interrupt broadcasts reaching all active threads across the memory manifold.
4. Author `src/ccscript/cow_epilogue.ccs`: Clean kernel reboot, memory barrier release, homecoming in Onett, and epilogue dispatch (Sector 38, `flag 933`).
5. Update `src/ccscript/cow_engine.ccs`: Allocate Sector dirty bits 932 (Cave of the Past) and 933 (Epilogue/Reboot), Entity mutation bits 934-938, and corresponding commit subroutines.
6. Rebalance final boss and late-game enemies in `src/enemy_configuration_table.yml`, enforce dual-binding dispatch across NPC table entries and legacy trampolines, and expand `tools/verify_rom.py`.
**Alternatives:** Retaining vanilla abstract metaphysical cosmic horror dialogue without systems architecture metaphor (breaks core premise).
**Consequences:** Resolves the entire narrative arc as a cosmic debugging operation restoring system integrity and committing the final clean kernel state. Automated verification in `tools/verify_rom.py` expanded to 245 binary assertions.
**Review trigger:** Verification of end credits and epilogue save state.

## D-022 Checkpoint SRAM Architecture and Headless Assertion Framework (2026-11-17, status: accepted)
**Context:** Rapidly proving game mechanics, dirty-page mutations, and late-game encounters across 15 development phases without requiring a 40-hour manual playthrough.
**Decision:**
1. Implement `tools/generate_saves.py` creating an 8,192-byte battery SRAM (`eb_zero_fault.srm`) containing three distinct progression checkpoints across primary and mirror blocks (6 blocks total):
   - Slot 1: Mid-game checkpoint (Phase 9/10 Fourside monolithic kernel & Moonside bitwise-NOT inversion, Level 45).
   - Slot 2: Late-game checkpoint (Phase 13 Magicant core dump & Sea of Eden root mutex lock, Level 75).
   - Slot 3: Endgame checkpoint (Phase 15 Cave of the Past robotic chassis & Giygas hypervisor singularity, Level 99).
2. Compute exact dual checksums (Checksum 1: cumulative byte sum mod 0x10000; Checksum 2: 16-bit word XOR) for both primary and mirror blocks.
3. Implement `tools/test_headless_assertions.py` executing 81 automated headless runtime and state assertions covering SRAM checksum integrity, party coordinates, B-button dash 65816 assembly vectors, fast-text delay calculation, HDMA queue safety, shop stat differential math, and CoW dirty-page state isolation.
**Alternatives:** Relying solely on manual playthroughs in GUI emulators or basic static string checks.
**Consequences:** Enables instantaneous spot-checking in Snes9x at any chapter and establishes automated headless CI/CD assertion testing.
**Review trigger:** Modifying SRAM layout or adding new gameplay mechanics.

## D-023 Architectural PSI and Diagnostic Hardware Overhaul (2026-11-17, status: accepted)
**Context:** Aligning battle abilities, PSI spells, and Jeff's unique hardware tools with the low-level operating system architecture and hardware probe motifs of EarthBound: Zero Fault (P16-01 through P16-03).
**Decision:**
1. Update `src/psi_name_table.yml` renaming offensive, defensive, and recovery PSI spells:
   - PSI Fire to PSI Fork
   - PSI Freeze / Flash to PSI SIGKILL / PSI SIGBUS
   - PSI Shield to Mutex Lock / Kernel Mutex
   - Lifeup / Healing to PSI Flush / Heap Clean / PSI Defrag
   - Brainshock to Core Dump
2. Update `src/ccscript/data_05.ccs` and `src/ccscript/data_56.ccs` battle help and invocation descriptions to match system architecture semantics.
3. Retool Jeff's hardware kit in `src/item_configuration_table.yml`:
   - Item 131: Bus Analyzer (replaces Spy / Slime Generator)
   - Item 138: Logic Probe (replaces Defense Shower)
   - Item 145: Interrupt Vector (replaces Big Bottle Rocket)
   - Item 206: Worn Polarized Lens (replaces Insignificant Item in Ness's starting bedroom desk)
4. Update item help pointers in `src/ccscript/data_03.ccs` and `src/ccscript/data_04.ccs`.
5. Expand headless assertion suite `tools/test_headless_assertions.py` to 94 tests and `tools/verify_rom.py` to 258 binary assertions.
**Alternatives:** Retaining vanilla whimsical PSI names and generic bottle rockets while only modifying overworld dialogue (inconsistent ludonarrative framing).
**Consequences:** Seamlessly unifies active battle mechanics and equipment menus with the core systems architecture premise without breaking existing game balance or damage algorithms.
**Review trigger:** Implementing Phase 17 memory pressure flush loop and status fault triggers.

## D-024 Volatile Sector Memory Pressure Engine, Flush Hooks, and Visual Compaction (2026-11-17, status: accepted)
**Owner:** Gordon (Custodian)
**Context:** To mechanically tie the Copy-on-Write memory narrative to gameplay without punishing players, accumulated sector mutations must create mounting volatile memory pressure that manifests in dynamic overworld glitch effects and a combat hazard, while providing intuitive release valves (saving at payphones, resting at hotels, using garbage collectors).
**Decision:**
1. Author assembly memory pressure engine in `src/ccscript/cow_pressure.ccs` operating on RAM `$7E9C40`:
   - Clamped pressure scale: 0 to 10.
   - Increment routines: `CowPressure_Inc1`, `CowPressure_Inc2`.
   - Relief routines: `CowPressure_Half` (50% reduction via bitwise right shift), `CowPressure_Reset` (cleared to 0), `CowPressure_Shed3` (reduction by 3).
2. Install universal event flag interception hook at SNES `$C21669` (ROM offset `0x021669`) in `SET_EVENT_FLAG`, incrementing pressure (+2) when mutating CoW sector flags 850..938, and clearing pressure to 0 when resting at hotels (flag 169).
3. Install universal payphone save interception hook at SNES `$C185DA` (ROM offset `0x0185DA`), intercepting `{save}` (`[1F B0]`) and cutting volatile pressure in half on every record commit.
4. Retool Item 111 into *Garbage Collector* (cost: $35) to manually shed 3 pressure units.
5. Couple visual thrashing to overworld movement via `src/ccscript/dash.ccs` (`InRunMode`): scanline jitter (pressure >= 4), palette shift (pressure >= 7), and wavy distortion (pressure == 10).
6. Install combat hazard in battle loop at pressure 10 (10% Page Fault Latency).
7. Update Dad's save dialogue (`src/ccscript/data_17.ccs`) and hotel morning dialogue (`src/ccscript/data_44.ccs`).
**Alternatives:** Permanent memory degradation that bricks saves or softlocks gameplay (hostile player friction).
**Consequences:** Establishes a tangible ludic loop between dirty sector accumulation, perceptual corruption, and regular memory compaction habits.
**Review trigger:** Playtesting Phase 18 and Phase 19 overworld chapters with volatile memory pressure active.

## D-025 Deconstructed Awakening & Physical Media Decay Audio Pipeline (2026-11-17, status: accepted)
**Owner:** Gordon (Custodian)
**Context:** To establish the final loop premise from the first frame of gameplay, the bombastic vanilla meteor crash sequence must be replaced with an uncanny silent cold open, an impossible persistent artifact (*Worn Polarized Lens*) in Ness's starting bedroom desk drawer, weary motherly dialogue acknowledging Ness's prior lifetime, Pokey's astonishment that Ness opens the front door before he raises his fist, and an active chronological physical media audio decay engine.
**Decision:**
1. Script `cow_cold_open` in `src/ccscript/cow_prologue.ccs` hooked at SNES `$C5E70B` (ROM offset `0x05E70B`), muting the audio engine and warping Ness directly to his bedroom in complete silence without the meteor explosion cutscene.
2. Script `cow_desk_drawer` hooked at SNES `$C8683D` (ROM offset `0x08683D`), granting key item 206 (*Worn Polarized Lens*) with dialogue conveying an impossible relic from a past journey.
3. Script `cow_tracy_awakening` hooked at SNES `$C66AA4` (ROM offset `0x066AA4`), with Tracy perceiving the eerie stillness and halted time.
4. Update `cow_mom_initial_awakening` and `cow_mom_awakening` in `src/ccscript/cow_onett.ccs` with weary, tender dialogue as Mom recognizes her son's ancient eyes and promises to hold his base pointer.
5. Update `cow_pokey_burst` in `src/ccscript/cow_onett.ccs`, having Pokey react in shock that Ness opened the door before he could knock and looks through him like a dead process.
6. Author assembly audio decay engine in `src/ccscript/cow_audio.ccs`:
   - Stage 0 (Act I: Onett to Threed): Subtle wow and flutter via 1-cent SPC pitch micro-drift.
   - Stage 1 (Act II: Fourside to Scaraba): Capstan drag with tempo/pitch degradation.
   - Stage 2 (Act III: Deep Darkness to Past): Severe high-frequency attenuation and music box timbre.
   - Dispatched per-step inside `InRunMode` in `src/ccscript/dash.ccs`.
7. Expand `tools/verify_rom.py` to 271 assertions and `tools/test_headless_assertions.py` to 120 assertions.
**Alternatives:** Retaining vanilla meteor crash sequence and conventional soundtrack (fails to establish the final loop ludonarrative framing from the outset).
**Consequences:** Sets an immediate, haunting atmosphere from the initial boot, establishing that the 30-year cartridge substrate has reached its final cycle.
**Review trigger:** Implementing Phase 19 memory leak dungeons and superboss encounters.

## D-026 Memory Leak Dungeons & Architectural Superboss Encounters (2026-11-17, status: accepted)
**Owner:** Gordon (Custodian)
**Context:** To provide ultimate endgame challenges that mechanically exercise the memory architecture and provide late-game utility before the Cave of the Past, three optional memory leak dungeons are introduced: Abandoned Swap Space, Unallocated Heap, and Legacy Boot ROM. Each dungeon features high-threat superboss encounters guarding tier-5 hardware artifacts.
**Decision:**
1. Configure three endgame hardware artifacts in `src/item_configuration_table.yml` and `src/ccscript/data_04.ccs`:
   - Item 140 (*Solid State Band*): Jeff-exclusive arm gear granting +45 Defense and elemental/status resistances.
   - Item 143 (*Heap Compactor*): Battle usable item restoring 50 PP.
   - Item 154 (*Kernel Privilege Ring*): Ness-exclusive accessory granting +30 Defense and +50 Guts.
2. Configure three superboss encounters in `src/enemy_configuration_table.yml` and `src/enemy_groups.yml`:
   - Enemy 198 (*Thrashing Hypervisor*, Group 460): 8400 HP, 650 PP, 185 Offense, 160 Defense, 1 Speed, drops Item 140.
   - Enemy 217 (*Garbage Collector Prime*, Group 461): 11200 HP, 900 PP, 210 Offense, 195 Defense, 60 Speed, drops Item 143.
   - Enemy 230 (*Monolithic BIOS Kernel*, Group 462): 14000 HP, 1200 PP, 240 Offense, 255 Defense, 40 Speed, drops Item 154.
3. Author dungeon interaction scripts in `src/ccscript/cow_dungeons.ccs`:
   - Abandoned Swap Space (SNES `$C8F75E`, ROM offset `0x08F75E`, NPC 481): Clears Flag 901 upon defeat.
   - Unallocated Heap (SNES `$C9ED3C`, ROM offset `0x09ED3C`, NPC 1238): Clears Flag 902 upon defeat.
   - Legacy Boot ROM (SNES `$EF6084`, ROM offset `0x2F6084`, NPC 1294): Enforces ring-0 privilege verification requiring Item 138 (*Logic Probe*) before granting execution clearance, setting Flag 903 upon defeat.
4. Establish dual bindings via both `src/npc_config_table.yml` text pointer reassignments and direct ROM label vector hooks (`ROM[...] = goto(...)`).
5. Expand `tools/verify_rom.py` to 286 binary assertions and `tools/test_headless_assertions.py` to 138 headless runtime assertions.
**Alternatives:** Reusing vanilla Sanctuary boss encounters without thematic memory corruption or hardware requirements.
**Consequences:** Introduces high-tier post-game content that organically integrates with the OS corruption narrative and tests endgame party loadouts.
**Review trigger:** Playtesting superboss difficulty tuning and item balance during Phase 21 full verification.

## D-027 Interactive Terminal Unmount Epilogue & Final Graceful Shutdown (2026-11-17, status: accepted)
**Owner:** Gordon (Custodian)
**Context:** The philosophical climax of *EarthBound: Zero Fault* resolves Ness's 30-year recursive loop. Rather than hanging on a static "THE END?" screen, the ending provides a quiet twilight return to Onett, giving the player unhurried freedom to explore a peaceful, static world before returning to Ness's bedroom, extinguishing the nightstand lamp, and executing an authentic 65816 CPU hardware halt (`STP` opcode).
**Decision:**
1. Author Paula's farewell sequence in `src/ccscript/cow_epilogue.ccs` (`cow_epilogue_paula_farewell`) hooked at SNES `$C7FC3E` (ROM offset `0x07FC3E`) and `src/ccscript/data_35.ccs`, acknowledging the quiet network bus, the lifting of all race conditions, and urging Ness to rest his registers.
2. Hook end credits conclusion in `src/ccscript/cow_epilogue.ccs` (`cow_epilogue_post_credits`) at SNES `$C9C98A` (ROM offset `0x09C98A`) and `src/ccscript/data_53.ccs`, setting post-credits twilight Flag 939, muting background music to ambient tape hiss, and warping Ness to his bedroom (`warp 196`).
3. Author bedtime dialogues for Mom (`cow_mom_post_credits`) and Tracy (`cow_tracy_post_credits`) in `src/ccscript/cow_epilogue.ccs` under Flag 939, comforting Ness that all resident pages are committed and that Mom will hold his base pointer.
4. Add bedside lamp interaction triggers in `src/map_doors.yml` (sector 36, 27) and `src/ccscript/data_39.ccs` (`l_cow_bedside_lamp`) dispatching `cow_bedside_lamp`, offering the prompt "Turn off the light and go to sleep?". Selecting No keeps the room illuminated; selecting Yes initiates system unmount narration ("Unmounting /dev/snes0... <OK>", "Flushing dirty sectors... <OK>", "Refcount reached zero.", "All threads terminated.", "System halted.", "Goodnight, Ness.") and sets Flag 940.
5. Author 65816 assembly graceful shutdown routine `GracefulShutdown_STP` in `src/ccscript/cow_pressure.ccs`: disables interrupts (`SEI`), blanks screen via PPU forced blanking (`INIDISP = $80`), silences audio ports (`$2140..$2143`), and stops CPU instruction fetching via `STP` opcode (`$DB`) with a fallback branch loop. Intercept Flag 940 in `HookFlagMutation` at SNES `$C21669`.
6. Expand `tools/verify_rom.py` to 299 binary assertions and `tools/test_headless_assertions.py` to 156 headless runtime assertions.
**Alternatives:** Endless loop on final picture screen (vanilla behavior that leaves the CPU running indefinitely without narrative closure).
**Consequences:** Provides an emotionally resonant, authentic hardware conclusion where the SNES processor ceases execution, symbolizing total rest.
**Review trigger:** Full regression verification during Phase 21.

## D-028 Full Verification, Regression Integrity & Project Delivery (2026-11-17, status: accepted)
**Owner:** Gordon (Custodian)
**Context:** With all 20 development phases implemented—ranging from toolchain decompilation and QoL mechanics through Copy-on-Write state mutation, narrative overhaul, memory leak dungeons, and the graceful terminal unmount epilogue—Phase 21 provides exhaustive regression testing, companion re-indexing, doc checking, and final repository synchronization.
**Decision:**
1. Execute full binary verification via `tools/verify_rom.py`, verifying all 299 assertions covering ROM header integrity, 131 low-level hooks, 3 ATM debug vectors, 56 dynamic active NPC pointers, 97 encoded thematic entities, and the `GracefulShutdown_STP` machine code block (SEI `$78` and STP `$DB`).
2. Execute full headless assertion suite via `tools/test_headless_assertions.py`, verifying all 156 assertions covering SRAM 3-slot checksums and coordinates, B-button dash speed normalization, fast-text subframe delay bypassing, shop stat differential arithmetic, CoW dirty-page bitfield invariants (flags 836..1023), volatile memory pressure scaling and compaction release valves, SPC700 physical media decay audio drift calculations, prologue hooks, superboss dungeon cleared flags (901..903), and terminal shutdown flags (939..940).
3. Re-index all game data, decompiled scripts, and table configurations into the self-contained Zero Fault Companion single-file HTML application (`tools/zero_fault_companion.html`, 5.0 MB) and synchronize with the persistent conversation artifact directory.
4. Verify documentation integrity via `tools/check_docs.py`, guaranteeing zero errors and zero warnings across all 14 project documents and archived session logs.
5. Deploy all source changes, tests, and documentation cleanly to GitHub (`aedmark/eb-zero-fault.git`) on branch `main`.
**Alternatives:** Manual spot checking on an emulator (insufficient to catch boundary overflows, corrupted pointers, or regression failures across 20 phases).
**Consequences:** Assures complete binary, engine, and documentation integrity across the entire project with zero regressions.
**Review trigger:** Future community contributions or packaging for physical SNES cartridge flashing.

## D-029 Prologue Cold Open Architecture, Sector Mapping, and Hardware Invariants (2026-11-17, status: accepted)
**Owner:** Gordon (Custodian)
**Context:** The prologue cold open must start Ness in his bed in complete stillness and silence, wearing pajamas, without meteor explosions, screen vibration, sirens, or door sound effects, and with the Logic Probe (Item 138) and Worn Polarized Lens (Item 206) in his desk drawer. Initial playtesting revealed visual blips, daytime clothing, screen oscillation, door impact audio, and unmapped furniture triggers.
**Decision:**
1. Dual Bedroom Sector Disambiguation: EarthBound maps Ness's bedroom into two distinct sectors: nighttime (intro) at Sector Row 4, Col 31 (Warp 10, coordinates 1017, 137) and daytime at Sector Row 36, Col 27 (coordinates 888, 1165). NPC 28 (Desk Object at pixel coords 144, 48 in Sector 4, 31) had its Text Pointer 1 bound to `cow_prologue.cow_desk_drawer`. Sector 4, 31 and Sector 36, 27 in `src/map_doors.yml` were populated with door object triggers across tiles (17..19, 6..8) targeting `cow_prologue.cow_desk_drawer`.
2. Camera Shake Elimination: Discovered that vanilla movement script 36 (`0x0024`) at `$C3ACAD` contains a damped sine wave camera offset displacement table (+16, -31, +26, -23, +21, -19...). Eliminated `[1F 15 6A 00 24 00 01]` from `cow_cold_open`, and patched `ROM[0xC1FEBC]` with `STZ $4A66` to disable the intro camera earthquake.
3. Bedroom Door Sound Suppression: Leaving the nighttime bedroom through door (4, 10) invokes `l_0xc99930` which dispatches `l_0xc99945` (`[1F E1 10 03 1E]`, meteor impact sound) if Flag 517 is unset. Added `{set(flag 517)}` to `cow_cold_open` and replaced `l_0xc99945` in `src/ccscript/data_51.ccs` with silent flag commits.
4. House Audio Muting: Set `Music: 0` for Sectors 159 (bedroom), 125 (hallway), 126 (living room), and 127 (kitchen) in `src/map_sectors.yml` and silenced Track 17 in `src/map_music.yml`, ensuring unbroken ambient silence inside the residence.
5. Pajamas Sprite Refresh: Flag 749 (Pajamas) updates player graphics upon map reload. Initialized cold open sequence with `{hide_char(255)}`, `{set(flag 749)}`, `{set(flag 477)}`, and `{warp(10)}` before pausing for waking sprite and revealing the party with `{show_party(1)}` and movement script 626 (step out of bed), preventing player sprite blips or daytime clothes.
**Alternatives:** Attempting to force sprite indices in RAM without warp refresh (leads to corrupted tile DMA and sprite glitching).
**Consequences:** The prologue begins in pure stillness and silence, Ness awakens in bed in pajamas, and both items are immediately obtainable from the desk drawer.
**Review trigger:** Testing prologue progression across various SNES emulator cores.

---

## Held tensions

### T-001 Expanded ROM Size vs Strict Hardware Compatibility (2026-11-14, status: held)
**Owner:** Gordon (Custodian)
**Claim A:** Expanding the ROM to 32 Mbits (4 MB) or 48 Mbits provides abundant space for uncompressed text, custom audio banks, and expanded event scripting.
**Claim B:** Strict adherence to 24 Mbits (3 MB) guarantees parity with original cartridge flash configurations and older SNES flash carts.
**Why both hold:** Large-scale script expansion demands headroom, but hardware preservation requires broad target compatibility.
**Cost of holding both:** Compiling remains targeted at default CoilSnake expansion while tracking memory budget.
**Review trigger:** ROM space consumption exceeding 24 Mbits during Phase 4 script authoring.

---

## Open questions

- **Q-001** Should the B-Button Dash be permitted inside interiors and caves, or restricted to outdoor town maps to preserve spatial scale? Answer: Option B (Outdoors only). Restrict dash to outdoor maps via native collision check to preserve spatial scale and interior pacing (2026-11-14, D-006).

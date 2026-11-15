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

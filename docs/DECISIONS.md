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

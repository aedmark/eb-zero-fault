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

Last updated: 2026-11-14, session 2, on `main`: Phase 1 complete. Toolchain configured in `.venv`, clean ROM decompiled into `src/` (tables, maps, graphics, and 62 CCScript modules), and `tools/build.sh` verified producing 4,194,304-byte expanded ROM.

**Session owner:** Antigravity / Maintainer, on `main`, since 2026-11-14. Phase 1 completion and Phase 2 QoL integration.

**Where things stand, in one paragraph:** Phase 1 is fully complete. CoilSnake 4.3 and native compilation tools (`ccscript`, `CCScriptWriter`) are built and verified inside `.venv`. The clean EarthBound ROM has been fully decompiled into `src/`, including all game balance YAML tables, tilesets, sprites, and 62 CCScript dialogue and event modules. An automated build pipeline (`tools/build.sh`) cleanly provisions an ephemeral 32-Mbit base ROM and compiles the project to `build/eb_zero_fault.sfc` in 6.52 seconds without touching the root reference ROM.

**Verified** (2026-11-14, CachyOS Linux x86-64-v3, Python 3.14.10)

| Suite | Result |
| --- | --- |
| `python3 tools/check_docs.py` | Pass (0 errors, 0 warnings) |
| ROM size check (`stat -c %s "EarthBound (USA).sfc"`) | Exactly 3,145,728 bytes |
| Baseline compilation (`tools/build.sh`) | Pass (4,194,304 bytes, 6.52s) |

**What works**
- **Toolchain & Base Decompilation** (P1-01, P1-02, P1-03, P1-04, D-001, D-002, D-005). Complete source tree in `src/` with round-trip compilation verified via `tools/build.sh`.
- **Repository Harness** (`tools/check_docs.py`, `AGENTS.md`, `ROADMAP.md`, `docs/DECISIONS.md`). Documentation cross-references and invariants are fully validated.

**Not verified**
- GUI emulator runtime inspection (pending emulator installation via pacman on CachyOS).

**Gotchas for the next session**
- Host OS is CachyOS (Arch Linux base). Use `pacman` or `paru`, never `apt`.
- Always use `tools/build.sh` for compilation to ensure the ephemeral 32-Mbit base target is handled cleanly without modifying the root reference ROM.
- Never edit or compile directly into `EarthBound (USA).sfc`.

## Next steps (in order)

1. Clarify Q-001 regarding indoor B-Button Dash behavior before implementation.
2. Implement modular B-Button Dash movement script in `src/ccscript/` (P2-01).
3. Implement fast text print routine in CCScript (P2-02).
4. Verify compiled ROM in an emulator (P2-04).

## Open questions for maintainers

- Q-001 Should the B-Button Dash be permitted inside interiors and caves, or restricted to outdoor town maps to preserve spatial scale? Blocks P2-01.

## Session log

### Session 2 (2026-11-14)
Completed Phase 1. Built CoilSnake 4.3 natively with ccscript and CCScriptWriter on Python 3.14 (P1-02). Executed clean ROM decompile and scriptdump generating `src/` asset tree and 62 CCScript data modules (P1-03). Formulated decision D-005 and automated ephemeral 32-Mbit intermediate base compilation via `tools/build.sh`, producing clean 4,194,304-byte output `build/eb_zero_fault.sfc` in 6.52 seconds (P1-04).

### Session 1 (2026-11-14)
Formalized project repository under The Manifold and Hypervisor. Verified base ROM file size (3,145,728 bytes unheadered) satisfying P1-01 and D-002. Drafted initial roadmap phases P1 through P6, architectural specifications, decisions D-001 through D-004, and validated documentation integrity via `tools/check_docs.py`.

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

Last updated: 2026-11-14, session 3, on `main` (`0135103`): Q-001 resolved via D-006 (Option B: Outdoors only). P2-01 implemented in `src/ccscript/dash.ccs` and compiled cleanly to `build/eb_zero_fault.sfc`.

**Session owner:** Antigravity / Maintainer, on `main`, since 2026-11-14. Phase 2 QoL implementation.

**Where things stand, in one paragraph:** Option B was selected for Q-001, restricting the B-Button Dash to outdoor areas where bicycles are permitted (D-006). The complete 65816 assembly macro library (`src/ccscript/asm65816.ccs`) was added, and the B-Button Dash module (`src/ccscript/dash.ccs`) was implemented and compiled into `build/eb_zero_fault.sfc`. Binary verification confirms the three movement speed and animation routine hooks at `0xC02F30`, `0xC031B8`, and `0xC07960`. The next task is P2-02 (accelerated text printing routine).

**Verified** (2026-11-14, CachyOS Linux x86-64-v3, Python 3.14.10)

| Suite | Result |
| --- | --- |
| `python3 tools/check_docs.py` | Pass (0 errors, 0 warnings) |
| ROM compilation (`tools/build.sh`) | Pass (4,194,304 bytes, 6.58s) |
| Binary hook verification (Python script) | Verified `JSL InRunMode` at `0xC02F30`, `0xC031B8`, and `0xC07960` |

**What works**
- **Toolchain & Base Decompilation** (P1-01 through P1-04, D-001, D-002, D-005). Complete source tree in `src/` and reproducible automated build via `tools/build.sh`.
- **Outdoor-Only B-Button Dash** (P2-01, D-003, D-006; `src/ccscript/dash.ccs`). Player runs at double speed while holding B outdoors, retains normal walk indoors, and preserves vanilla Skip Sandwich behavior.
- **Repository Harness** (`tools/check_docs.py`, `AGENTS.md`, `ROADMAP.md`, `docs/DECISIONS.md`). All invariants, decisions, and IDs remain consistent.

**Not verified**
- Interactive emulator control feel on hardware (pending emulator installation on host).

**Gotchas for the next session**
- Host OS is CachyOS (Arch Linux base). Use `pacman` or `paru`, never `apt`.
- Always compile using `tools/build.sh`.

## Next steps (in order)

1. Implement accelerated text printing routine and dialogue skip flag (P2-02).
2. Implement shop equipment stat differential comparison display (P2-03).
3. Test compiled ROM in an emulator (P2-04).

## Open questions for maintainers

None currently blocking.

## Session log

### Session 3 (2026-11-14)
Resolved Q-001 in favor of Option B (Outdoors only) per maintainer directive, formalizing D-006. Imported 65816 assembly macro library `src/ccscript/asm65816.ccs`. Implemented `src/ccscript/dash.ccs` hooking controller 1 polling (`0x0066` high byte, mask `0x0080`) and native collision check `CHECK_BICYCLE_COLLISION_FLAGS` (`0xC03C4B`) at `0xC02F30`, `0xC031B8`, and `0xC07960`. Compiled `build/eb_zero_fault.sfc` in 6.58 seconds, verified binary injection, and marked P2-01 done.

### Session 2 (2026-11-14)
Completed Phase 1. Built CoilSnake 4.3 natively with ccscript and CCScriptWriter on Python 3.14 (P1-02). Executed clean ROM decompile and scriptdump generating `src/` asset tree and 62 CCScript data modules (P1-03). Formulated decision D-005 and automated ephemeral 32-Mbit intermediate base compilation via `tools/build.sh`, producing clean 4,194,304-byte output `build/eb_zero_fault.sfc` in 6.52 seconds (P1-04).

### Session 1 (2026-11-14)
Formalized project repository under The Manifold and Hypervisor. Verified base ROM file size (3,145,728 bytes unheadered) satisfying P1-01 and D-002. Drafted initial roadmap phases P1 through P6, architectural specifications, decisions D-001 through D-004, and validated documentation integrity via `tools/check_docs.py`.

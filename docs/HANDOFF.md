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

Last updated: 2026-11-14, session 1, on `main`: project formalized under The Manifold and Hypervisor. Base ROM verified; source tree decompile pending.

**Session owner:** Antigravity / Maintainer, on `main`, since 2026-11-14. Project formalization and toolchain setup.

**Where things stand, in one paragraph:** The project repository is formalized using The Manifold and Hypervisor templates. A clean, unheadered North American EarthBound base ROM is present and verified at exactly 3,145,728 bytes (P1-01). Foundational architecture, roadmap items, decision records, and test protocols are established. The immediate next action is setting up a Python virtual environment on CachyOS and executing the clean decompile into `src/`.

**Verified** (2026-11-14, CachyOS Linux x86-64-v3, Python 3.14.10)

| Suite | Result |
| --- | --- |
| `python3 tools/check_docs.py` | Pass |
| ROM size check (`stat -c %s "EarthBound (USA).sfc"`) | Exactly 3,145,728 bytes |

**What works**
- **Base ROM Verification** (P1-01, D-002; `EarthBound (USA).sfc`). Clean unheadered 3.0 MB ROM confirmed ready for decompiler ingestion.
- **Repository Harness** (`tools/check_docs.py`, `AGENTS.md`, `ROADMAP.md`). Documentation cross-references and invariants are fully validated.

**Not verified**
- CoilSnake execution and clean decompile on Python 3.14 / CachyOS environment.

**Gotchas for the next session**
- Host OS is CachyOS (Arch Linux base). Use `pacman` or `paru`, never `apt`.
- CoilSnake must be installed inside an isolated virtual environment (`.venv`), not globally via sudo.
- Never edit or compile directly into `EarthBound (USA).sfc`.

## Next steps (in order)

1. Set up Python virtual environment `.venv` and install `coilsnake` (P1-02).
2. Decompile `EarthBound (USA).sfc` into `src/` via `coilsnake decompile` (P1-03).
3. Execute dry-run baseline compilation from `src/` to confirm round-trip stability (P1-04).

## Open questions for maintainers

- Q-001 Should the B-Button Dash be permitted inside interiors and caves, or restricted to outdoor town maps to preserve spatial scale? Blocks P2-01.

## Session log

### Session 1 (2026-11-14)
Formalized project repository under The Manifold and Hypervisor. Verified base ROM file size (3,145,728 bytes unheadered) satisfying P1-01 and D-002. Drafted initial roadmap phases P1 through P6, architectural specifications, decisions D-001 through D-004, and validated documentation integrity via `tools/check_docs.py`.

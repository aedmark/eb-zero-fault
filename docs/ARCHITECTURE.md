# Architecture

How EarthBound: Zero Fault fits together, for a session that has never seen it. This is the map, not the territory:
it names the parts and the rules between them, and leaves the detail to the code. Keep it short enough to read in five
minutes; update it when the shape changes (a module added, moved or merged), not for every change inside one.

Why things are this way lives in [DECISIONS.md](DECISIONS.md); this file says *what* is, and points there.

## The shape, in one paragraph

The build pipeline ingests plain text CCScript files, YAML balance tables, and indexed PNG graphics from `src/`,
verifies them against hardware constraints, and compiles an expanded 32-Mbit SNES ROM binary into `build/` using
CoilSnake (D-001). The game engine executes on SNES hardware or emulators, reading dirty-page event flags
(D-004) to conditionally fork narrative branches and entity behaviors dynamically whenever a player interacts
with an uncommitted world sector.

## Code map

Where to look for what. One row per area a session might need to find; name the entry point, not every file.

| Area | Where | Entry point | Talks to |
| --- | --- | --- | --- |
| Base ROM | `EarthBound (USA).sfc` | Base binary file | Decompiler input reference; read-only |
| Source Tree | `src/` | Project root | CoilSnake compilation entry point |
| Event Scripts | `src/ccscript/` | `main.ccs` | EarthBound script bytecode interpreter |
| Game Tables | `src/yml/` | Configuration YAMLs | Monster, item, and ability balance structures |
| Graphics | `src/graphics/` | Indexed PNG sheets | SNES VRAM tile and palette importer |
| Build Output | `build/` | `eb_zero_fault.sfc` | SNES emulator or flash hardware |

## Interfaces and data flow

Describe stable interfaces and the direction data moves.

```text
EarthBound (USA).sfc -> CoilSnake decompile -> src/ -> CCScript/YAML edits -> CoilSnake compile -> build/eb_zero_fault.sfc -> Mesen-S
```

| Interface | Producer | Consumer | Contract / compatibility |
| --- | --- | --- | --- |
| Base ROM | Legal cartridge dump | CoilSnake decompiler | Exactly 3,145,728 bytes unheadered (D-002) |
| CCScript files | Developer / Agent | CoilSnake compiler | CCScript syntax, valid flag and memory offsets |
| YAML data tables | Developer / Agent | CoilSnake compiler | Strict schema matching EarthBound internal tables |
| Target ROM | CoilSnake compiler | SNES Emulator / Hardware | Valid SNES cartridge header, internal checksum |

## Invariants

Rules that hold everywhere and that a change must not break. Each names what enforces it.

- The base ROM `EarthBound (USA).sfc` is read-only and never modified in-place. Enforced by: file permissions and AGENTS.md protected area rules (D-002).
- All gameplay modifications must be reproducible from source files in `src/`. Enforced by: automated clean build from source.
- Dirty page flags must reside in the allocated upper block `0x0300` through `0x03FF`. Enforced by: CCScript macro definitions (D-004).
- Documentation cross-references and placeholders must pass consistency checks. Enforced by: `python3 tools/check_docs.py`.

## Boundaries

Where outside data comes in and what is trusted on each side.

| Boundary | Comes in as | Checked by | Rule |
| --- | --- | --- | --- |
| Base ROM | `.sfc` binary | File size check | Must match 3,145,728 bytes; never headered |
| Script inputs | `.ccs` text files | CCScript preprocessor | Syntax validation and label resolution during compilation |
| Table configs | `.yml` text files | PyYAML parser in CoilSnake | Strict type and range validation against EarthBound specifications |
| Target binary | `.sfc` compilation | Emulator loader | Header validation, valid 65816 reset vectors |

## Dependencies

Everything the project needs that it did not write.

| Dependency | Version | For | Why this one (and not writing it) |
| --- | --- | --- | --- |
| CoilSnake | Latest stable | Disassembly and compilation | Established standard for EarthBound modification (D-001) |
| Python 3 | 3.10+ | Toolchain runtime | Cross-platform standard required by CoilSnake |
| Mesen-S | Latest | Emulation and verification | High hardware accuracy, live memory viewer, and CPU debugging |

# EarthBound: Zero Fault

An EarthBound (SNES) ROM hack exploring a copy-on-write parallel universe alongside modern engine Quality of Life improvements. Built for personal research and play.

## Premise

In standard memory management, a copy-on-write (CoW) page remains shared and read-only until an entity attempts modification; at that moment, an isolated private copy is allocated. 

In *EarthBound: Zero Fault*, Ness awakens in an uncommitted baseline reality. As long as entities and sectors remain untouched, they exist in a shared, frozen state. The moment Ness interacts with an NPC, opens a container, or triggers a battle, a memory fault occurs. The targeted sector commits to private storage, introducing subtle discrepancies, reference-count awareness, and narrative divergence.

## Features

- **Quality of Life Baseline**: Modular B-Button Dash, accelerated dialogue printing, and shop stat differentials.
- **Copy-on-Write Event Mechanics**: Event flag tracking representing dirty pages and state commits across Eagleland.
- **Thematic Reskinning**: Memory management and system architecture metaphors in enemies, consumables, and boss mechanics.
- **Source-Controlled Assets**: All scripts, YAML configuration tables, and graphics decompiled into human-readable source files via CoilSnake.

## Project Structure

This repository uses **The Manifold** documentation framework for durable repository memory across agent and human sessions, coupled with **The Hypervisor** cognitive harness.

| File | Owns |
| --- | --- |
| [`AGENTS.md`](AGENTS.md) | Standing agent rules, maintainer preferences, and repository map |
| [`CLAUDE.md`](CLAUDE.md) | Agent entry point importing AGENTS.md |
| [`ROADMAP.md`](ROADMAP.md) | Planned work with stable IDs (`P<phase>-<nn>`) |
| [`HYPERVISOR_V7.0.MD`](HYPERVISOR_V7.0.MD) | Cognitive and conversational harness contract |
| [`docs/HANDOFF.md`](docs/HANDOFF.md) | Current state, live owner, verified checks, and session log |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System shape, event flag schema, invariants, and boundaries |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | Append-only architectural decisions (`D-NNN`), tensions (`T-NNN`), and questions (`Q-NNN`) |
| [`docs/TESTING.md`](docs/TESTING.md) | Verification suites, emulator testing, and known failure modes |
| [`docs/SECURITY.md`](docs/SECURITY.md) | Base ROM protection, dump integrity, and distribution policy |
| [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) | Contributor and agent workflow |
| [`docs/CHANGELOG.md`](docs/CHANGELOG.md) | User-visible changes by version |
| [`tools/check_docs.py`](tools/check_docs.py) | Documentation consistency check tool |

## Quick Start (CachyOS / Arch Linux)

### 1. Prerequisites
Ensure Python 3 and build dependencies are present on CachyOS:
```bash
sudo pacman -S python python-pip git
```

### 2. Set Up Virtual Environment and Toolchain
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install coilsnake
```

### 3. Verify Base ROM
The base ROM file must be an unheadered North American EarthBound ROM of exactly 3,145,728 bytes:
```bash
ls -l "EarthBound (USA).sfc"
# Expected size: 3145728 bytes
```

### 4. Verification Check
Run the documentation test suite:
```bash
python3 tools/check_docs.py
```

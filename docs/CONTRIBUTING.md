# Contributing

Use this file for the workflow shared by human and automated contributors. Agent-specific standing instructions are
in [AGENTS.md](../AGENTS.md).

## Before changing code

1. Read the README, relevant roadmap item, architecture section, and test guidance. Verify the repository's actual
   conventions rather than importing external defaults.
2. Follow the setup in [README.md](../README.md#quick-start-cachyos--arch-linux).
3. Check `git status` and confirm that your change will not overlap unrelated work.
4. Surface unstated assumptions. For ambiguous requirements or a large change, ask clarifying questions
   (or record an open question in [DECISIONS.md](DECISIONS.md)) and agree on scope before implementation.

## Make the change

- Keep each change reviewable and focused on one outcome.
- If implementation or testing invalidates the agreed scope or exposes an unexpected architectural dependency, pause and
  re-scope before continuing.
- Preserve compatibility with the base ROM specifications (D-002).
- Update documentation according to [the documentation triggers](README.md#update-triggers).
- Do not commit ROM binary files or local cache directories.

## Verify

```bash
python3 tools/check_docs.py
coilsnake compile src/ build/eb_zero_fault.sfc
```

Follow [TESTING.md](TESTING.md) for prerequisites and suite limitations. Report the exact checks run and any checks
skipped.

## Submit and review

Direct-to-main workflow during initial single-developer research. All commits should use imperative present tense and
reference roadmap items where appropriate (e.g., `P1-01: verify clean ROM`).

## Compatibility and migrations

The project targets the North American EarthBound ROM (3,145,728 bytes). All script and table additions must remain
fully compatible with standard SNES hardware timing and memory configurations.

## Reporting security issues

Do not open a public issue for proprietary ROM matters. Follow [SECURITY.md](SECURITY.md).

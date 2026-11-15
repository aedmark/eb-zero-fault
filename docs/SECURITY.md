# Security

This document describes the project's security assumptions, asset boundaries, and intellectual property protections.

## Supported versions

| Version / branch | Security fixes |
| --- | --- |
| `main` | Active development branch |

## Report an issue

Report issues directly to the repository maintainer. Do not include proprietary ROM binaries or personal data.

## Assets and boundaries

| Asset or boundary | Sensitivity / threat | Protection and validation | Owner |
| --- | --- | --- | --- |
| Base ROM (`EarthBound (USA).sfc`) | Proprietary copyrighted game binary | Personal legal backup only; never committed to version control or distributed | Maintainer |
| Modded Output ROM (`build/*.sfc`) | Contains proprietary game assets | Excluded via `.gitignore`; strictly local testing | Maintainer |
| Repository scripts (`src/`) | Original creative work (CCScript, YAML, custom assets) | Version controlled; public license compatible | Maintainer |
| Delta patches (`.bps`) | Non-infringing distribution format | BPS patches contain only byte differentials, requiring user to supply clean ROM | Maintainer |

Architecture details belong in [ARCHITECTURE.md](ARCHITECTURE.md); this table records the security consequence.

## Secure development rules

- Never commit `.sfc`, `.smc`, or any Nintendo proprietary binary ROM files to version control.
- Validate file hashes and sizes before executing decompilers or patchers.
- Use isolated virtual environments for all Python tooling to avoid contaminating the system package manager on CachyOS.
- Ensure all distribution artifacts are strictly BPS delta patches.

## Security verification

- Automated check via `.gitignore` and `git status` ensuring no `.sfc` files are staged.
- Documentation check via `python3 tools/check_docs.py`.

## Incident response

If proprietary ROM binaries or credentials are accidentally committed: immediately purge them from git history using `git filter-repo` or `git filter-branch` before pushing to any remote repository.

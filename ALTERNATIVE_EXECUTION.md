# Alternative Execution Paths

GitHub environment gates are useful for controlled production promotion, but they are not the only way to verify Discrete.ai.

## Alternative A: Local full-stack verification

Run:

```bash
python -m pip install -e '.[dev]'
python -m pip install build
python scripts/alternative_verification.py
```

This path requires no GitHub environment, SSH host, production reviewer, or provider credential. It performs:

1. Repository-wide file validation.
2. Automated tests.
3. Python distribution build.
4. Full-stack production package build.
5. Temporary SQLite and storage creation.
6. Local Discrete.ai startup on port 8765.
7. `/api/health` and `/api/features` smoke tests.
8. Clean shutdown and removal of temporary state.

## Alternative B: Manual GitHub verification

Run **Actions → Alternative Verification**. It uses a standard GitHub-hosted runner but does not reference the `staging` or `production` environments. This separates code verification from deployment approvals.

## Alternative C: Self-hosted verification

A machine with Python 3.11+, Node.js, Bash, and repository access can execute the same command through a self-hosted runner or another automation system:

```bash
python scripts/alternative_verification.py
```

Examples include Jenkins, GitLab CI, Buildkite, TeamCity, Azure Pipelines, a scheduled systemd service, or a controlled local workstation.

## Alternative D: Artifact-only release candidate

The production package builder creates ZIP, TAR.GZ, wheel, source distribution, checksums, and a file manifest without deploying them. These artifacts can be manually reviewed, signed, transferred, or installed on an isolated host before production promotion.

## Alternative E: Direct host rehearsal

On a non-production Linux host:

```bash
python scripts/alternative_verification.py
python scripts/production_smoke_test.py http://127.0.0.1:8765
```

The SSH deployment scripts can then be tested against a temporary deployment root without GitHub environment administration.

## Interpretation of completion

A missing GitHub environment does not imply that code verification is zero percent. It means the GitHub-managed promotion route is unverified. Verification should be tracked separately across:

- implementation
- executable local verification
- hosted automation verification
- staging infrastructure verification
- production infrastructure verification

The alternatives improve confidence in the first three categories while preserving approval gates for actual production changes.

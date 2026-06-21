# DUPE Deployment

The DUPE operation creates a new immutable release from an existing deployed release without copying environment secrets, the SQLite database, or generated-image storage.

## Purpose

Use DUPE when a known-good release must be cloned under a new release identifier for controlled promotion, rollback testing, disaster-recovery rehearsal, or environment validation.

## Safety behavior

- Release identifiers accept only letters, numbers, dots, underscores, and hyphens.
- Source and target identifiers must differ.
- The source release must exist.
- The target release must not already exist.
- Partial copies are deleted when DUPE fails.
- Shared storage remains a symlink to `DEPLOY_ROOT/shared/storage`.
- Shared `.env` and SQLite data are never copied into a release.
- A `DUPE_MANIFEST.json` records source and target release identifiers.
- Normal migration, service restart, health-check, and rollback behavior runs after duplication.

## GitHub Actions execution

Open **Actions → DUPE Deployment → Run workflow** and provide:

- `environment`: `staging` or `production`
- `source_release`: an existing release directory name
- `target_release`: a new release directory name

Production DUPE runs through the protected `production` GitHub environment and therefore uses the same approval gate as a normal production deployment.

## Remote execution

The low-level operation is:

```bash
bash scripts/dupe_release.sh DEPLOY_ROOT SOURCE_RELEASE TARGET_RELEASE
```

To duplicate and promote the release through the full deployment lifecycle:

```bash
bash scripts/deploy_remote.sh ENVIRONMENT - DEPLOY_ROOT TARGET_RELEASE PORT SOURCE_RELEASE
```

Example:

```bash
bash scripts/deploy_remote.sh staging - /home/discrete/apps/staging release-2026-06-21-dupe 8001 release-2026-06-21
```

The service is switched only after the duplicate is prepared, installed, migrated, and configured. A failed health check restores the previous `current` release.

# Manual DUPE and DEDUPE Operations

The project no longer uses CI/CD automation or GitHub Actions deployment workflows. Releases are prepared, validated, duplicated, deduplicated, activated, and rolled back explicitly by an operator.

## Operating model

1. Build or identify a complete source release.
2. Run local validation.
3. Place the source under `DEPLOY_ROOT/releases/`.
4. Run `scripts/dupe_release.sh` with a new release identifier.
5. Verify `DUPE_MANIFEST.json`.
6. Run database migration and health checks manually.
7. Move the `current` symbolic link to the validated target.
8. Preserve the former target through `previous` for rollback.

## Host prerequisites

- Linux with Python 3.11 or newer
- `bash`, `tar`, `curl`, and OpenSSH when remote copying is needed
- user-level systemd support when running as a service
- write permission under the release root

## Release layout

```text
DEPLOY_ROOT/
├── current -> releases/current-release
├── previous -> releases/previous-release
├── incoming/
├── releases/
│   ├── source-release/
│   └── target-release/
└── shared/
    ├── .env
    ├── studio.db
    └── storage/
```

Shared state is not duplicated. The target release receives a symbolic link to `shared/storage`.

## Local validation

Run validation before creating a target release:

```bash
python scripts/check_all.py
python scripts/media_check.py
pytest
python -m build
```

Use strict media validation only when media integrity should block the operation:

```bash
python scripts/media_check.py --strict
```

## DUPE

```bash
bash scripts/dupe_release.sh DEPLOY_ROOT SOURCE_RELEASE TARGET_RELEASE
```

The handler validates release identifiers, refuses overwrite, copies the source, reconnects shared storage, verifies the complete CyGlobs Python Framework For Full Stack Developers and CyGlobsGL runtime, writes a manifest, and removes a partial target on failure.

## DEDUPE

The release model uses one canonical active `cyglobs_framework/` package. Reference snapshots and alternate framework identities are not used as runtime packages. `DUPE_MANIFEST.json` records:

```json
{
  "operation": "DUPE_AND_DEDUPE",
  "runtime": "CyGlobs Python Framework For Full Stack Developers",
  "renderer": "CyGlobsGL",
  "framework_injected": true,
  "cyglobsgl_injected": true,
  "external_provider": false,
  "dedupe_strategy": "single canonical active framework package"
}
```

## Activation

After validation:

```bash
ln -sfn "$DEPLOY_ROOT/current" "$DEPLOY_ROOT/previous"
ln -sfn "$DEPLOY_ROOT/releases/$TARGET_RELEASE" "$DEPLOY_ROOT/current"
systemctl --user restart cyglobs-studio.service
curl --fail http://127.0.0.1:8000/api/health
```

Adjust the service name and port to the host configuration.

## Rollback

When the health check fails:

```bash
PREVIOUS="$(readlink -f "$DEPLOY_ROOT/previous")"
ln -sfn "$PREVIOUS" "$DEPLOY_ROOT/current"
systemctl --user restart cyglobs-studio.service
```

No push, pull request, tag, workflow, environment gate, or hosted runner automatically changes a release.
